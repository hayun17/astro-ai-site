from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CORPUS_DIR = DATA_DIR / "corpus"
INDEX_PATH = DATA_DIR / "index.json"

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "to", "of", "in", "for", "on", "with", "as", "at", "by", "from",
    "this", "that", "these", "those", "it", "its", "be", "been", "being",
}

_word_re = re.compile(r"[a-zA-Z]+")


def tokenize(text: str) -> List[str]:
    tokens = [m.group(0).lower() for m in _word_re.finditer(text)]
    return [t for t in tokens if t not in STOPWORDS]


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


def _iter_corpus_files() -> List[Path]:
    """
    Recursively collect all .txt files under CORPUS_DIR.
    Supports folder structures like:
      corpus/placements/sun/sun_in_aquarius.txt
      corpus/rules/01_output_structure_extent.txt
    """
    if not CORPUS_DIR.exists():
        return []
    files = [p for p in CORPUS_DIR.rglob("*.txt") if p.is_file()]
    files.sort(key=lambda p: str(p).lower())
    return files


def build_index() -> List[DocChunk]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    chunks: List[DocChunk] = []
    files = _iter_corpus_files()

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw or len(raw) < 20:
            continue

        rel_source = path.relative_to(CORPUS_DIR).as_posix()

        for k, ch in enumerate(chunk_text(raw)):
            toks = tokenize(ch)
            tf: Dict[str, float] = {}
            for t in toks:
                tf[t] = tf.get(t, 0.0) + 1.0

            norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0

            chunks.append(DocChunk(
                id=f"{rel_source}:{k}",
                source=rel_source,
                text=ch,
                tf=tf,
                norm=norm,
            ))

    payload = [
        {"id": c.id, "source": c.source, "text": c.text, "tf": c.tf, "norm": c.norm}
        for c in chunks
    ]
    INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return chunks


def load_index() -> List[DocChunk]:
    if not INDEX_PATH.exists():
        return build_index()
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    chunks: List[DocChunk] = []
    for o in payload:
        chunks.append(DocChunk(
            id=o["id"],
            source=o["source"],
            text=o["text"],
            tf=o.get("tf", {}),
            norm=float(o.get("norm", 1.0)),
        ))
    return chunks


def cosine_sim(q_tf: Dict[str, float], q_norm: float, d_tf: Dict[str, float], d_norm: float) -> float:
    dot = 0.0
    for t, v in q_tf.items():
        dot += v * d_tf.get(t, 0.0)
    return dot / (q_norm * d_norm)


def retrieve(query: str, k: int = 5) -> List[Dict[str, str]]:
    chunks = load_index()
    toks = tokenize(query)
    q_tf: Dict[str, float] = {}
    for t in toks:
        q_tf[t] = q_tf.get(t, 0.0) + 1.0
    q_norm = math.sqrt(sum(v * v for v in q_tf.values())) or 1.0

    scored: List[Tuple[float, DocChunk]] = []
    for ch in chunks:
        s = cosine_sim(q_tf, q_norm, ch.tf, ch.norm)
        if s > 0:
            scored.append((s, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[Dict[str, str]] = []
    for s, ch in scored[:k]:
        out.append({
            "id": ch.id,
            "source": ch.source,
            "score": f"{s:.4f}",
            "text": ch.text,
        })
    return out
