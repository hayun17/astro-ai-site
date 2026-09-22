from __future__ import annotations

import json
import math
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CORPUS_DIR = DATA_DIR / "corpus"
INDEX_PATH = DATA_DIR / "index.json"

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "to", "of", "in", "for", "on", "with", "as", "at", "by", "from",
    "this", "that", "these", "those", "it", "its", "be", "been", "being",
}

# Keep digits and underscores so HOUSE_1 and HOUSE_12 remain distinct tokens.
_word_re = re.compile(r"[a-zA-Z0-9_]+")
_tag_re = re.compile(r"\[(TYPE|BODY|SIGN|KEY)=([^\]]+)\]", re.IGNORECASE)

_cache_lock = threading.RLock()
_index_cache: List["DocChunk"] | None = None
_corpus_signature_cache: Tuple[Tuple[str, int, int], ...] | None = None


def tokenize(text: str) -> List[str]:
    tokens = [m.group(0).lower() for m in _word_re.finditer(text or "")]
    return [t for t in tokens if t not in STOPWORDS]


def parse_metadata(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, value in _tag_re.findall(text or ""):
        out[key.upper()] = value.strip().upper()
    return out


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text] if text else []

    chunks: List[str] = []
    i = 0
    while i < len(text):
        end = min(len(text), i + max_chars)
        chunks.append(text[i:end])
        if end >= len(text):
            break
        i = max(0, end - overlap)
    return chunks


@dataclass
class DocChunk:
    id: str
    source: str
    text: str
    tf: Dict[str, float]
    norm: float
    metadata: Dict[str, str]


def _iter_corpus_files() -> List[Path]:
    if not CORPUS_DIR.exists():
        return []
    files = [p for p in CORPUS_DIR.rglob("*.txt") if p.is_file()]
    files.sort(key=lambda p: p.as_posix().lower())
    return files


def _corpus_signature(files: List[Path] | None = None) -> Tuple[Tuple[str, int, int], ...]:
    files = files if files is not None else _iter_corpus_files()
    sig = []
    for path in files:
        stat = path.stat()
        sig.append((path.relative_to(CORPUS_DIR).as_posix(), int(stat.st_size), int(stat.st_mtime_ns)))
    return tuple(sig)


def _build_chunks(files: List[Path]) -> List[DocChunk]:
    chunks: List[DocChunk] = []

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw or len(raw) < 20:
            continue

        rel_source = path.relative_to(CORPUS_DIR).as_posix()
        file_meta = parse_metadata(raw)

        for idx, ch in enumerate(chunk_text(raw)):
            toks = tokenize(ch)
            tf: Dict[str, float] = {}
            for token in toks:
                tf[token] = tf.get(token, 0.0) + 1.0
            norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0

            chunks.append(
                DocChunk(
                    id=f"{rel_source}:{idx}",
                    source=rel_source,
                    text=ch,
                    tf=tf,
                    norm=norm,
                    metadata=file_meta,
                )
            )

    return chunks


def build_index() -> List[DocChunk]:
    """Rebuild the index from the corpus and refresh the in-process cache."""
    global _index_cache, _corpus_signature_cache

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    with _cache_lock:
        files = _iter_corpus_files()
        chunks = _build_chunks(files)
        payload = [
            {
                "id": c.id,
                "source": c.source,
                "text": c.text,
                "tf": c.tf,
                "norm": c.norm,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _index_cache = chunks
        _corpus_signature_cache = _corpus_signature(files)
        return list(chunks)


def load_index() -> List[DocChunk]:
    """
    Return a fresh cached index.

    The old project trusted a committed index.json even when corpus files had
    changed. That left all house files invisible to retrieval. We now treat the
    corpus as the source of truth and rebuild automatically whenever its file
    signature changes.
    """
    global _index_cache, _corpus_signature_cache

    files = _iter_corpus_files()
    signature = _corpus_signature(files)

    with _cache_lock:
        if _index_cache is None or _corpus_signature_cache != signature:
            return build_index()
        return list(_index_cache)


def cosine_sim(q_tf: Dict[str, float], q_norm: float, d_tf: Dict[str, float], d_norm: float) -> float:
    dot = sum(v * d_tf.get(token, 0.0) for token, v in q_tf.items())
    return dot / (q_norm * d_norm)


def retrieve(query: str, k: int = 5) -> List[Dict[str, object]]:
    chunks = load_index()
    toks = tokenize(query)
    q_tf: Dict[str, float] = {}
    for token in toks:
        q_tf[token] = q_tf.get(token, 0.0) + 1.0
    q_norm = math.sqrt(sum(v * v for v in q_tf.values())) or 1.0
    q_tokens = set(q_tf)

    scored: List[Tuple[float, DocChunk]] = []
    for ch in chunks:
        score = cosine_sim(q_tf, q_norm, ch.tf, ch.norm)

        # Small deterministic boosts for structured metadata tokens. This keeps
        # exact placement/house documents ahead of merely related prose while
        # retaining generic lexical retrieval for rules and future corpus text.
        meta = ch.metadata
        for key in ("BODY", "SIGN", "KEY"):
            value = meta.get(key, "").lower()
            if value and value in q_tokens:
                score += 0.12

        if score > 0:
            scored.append((score, ch))

    scored.sort(key=lambda item: item[0], reverse=True)

    out: List[Dict[str, object]] = []
    for score, ch in scored[: max(0, k)]:
        out.append(
            {
                "id": ch.id,
                "source": ch.source,
                "score": round(score, 6),
                "text": ch.text,
                "metadata": ch.metadata,
            }
        )
    return out



def _cached_chunks() -> List[DocChunk]:
    # retrieve() refreshes the corpus signature once per interpretation request.
    # Exact/rule lookups that follow can reuse that cache without re-statting all
    # corpus files dozens of times.
    with _cache_lock:
        if _index_cache is not None:
            return list(_index_cache)
    return load_index()

def exact_passage(*, typ: str, body: str, sign: str) -> Dict[str, object] | None:
    """Find the first chunk whose structured tags exactly match the request."""
    typ_u, body_u, sign_u = typ.upper(), body.upper(), sign.upper()
    for ch in _cached_chunks():
        meta = ch.metadata
        if meta.get("TYPE") == typ_u and meta.get("BODY") == body_u and meta.get("SIGN") == sign_u:
            return {
                "id": ch.id,
                "source": ch.source,
                "score": 1.0,
                "text": ch.text,
                "metadata": meta,
                "forced": True,
            }
    return None


def rule_passages() -> List[Dict[str, object]]:
    """Return rule chunks in deterministic source order."""
    out: List[Dict[str, object]] = []
    for ch in _cached_chunks():
        if ch.source.startswith("rules/"):
            out.append(
                {
                    "id": ch.id,
                    "source": ch.source,
                    "score": 1.0,
                    "text": ch.text,
                    "metadata": ch.metadata,
                    "forced": True,
                }
            )
    out.sort(key=lambda p: str(p.get("source", "")))
    return out
