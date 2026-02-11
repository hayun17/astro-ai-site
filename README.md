# AstroAI Site (RAG-based Astrology Interpreter)

A **working** web app that:

1) Calculates a natal chart (planets, houses, major aspects) with **Swiss Ephemeris**.
2) Generates **original** interpretations using an LLM, optionally grounded on a **local text corpus** (RAG / retrieval-augmented generation).

Built as:
- **Backend:** FastAPI (Python)
- **Frontend:** Vite + React (TypeScript)

---

## Legal / ethical note (Tumblr & Reddit)
You asked to "collect all Tumblr astrology interpretations" and "collect Reddit comments". Automatically scraping/copying large amounts of platform content can violate Terms of Service and can raise copyright issues.

So this project is designed to be **safe by default**:
- It **does not scrape** Tumblr or Reddit.
- It lets you **add your own corpus** (texts you wrote, texts you have permission to use, public-domain texts, or content you export/download under the platform rules).
- The interpretation uses RAG: it will cite which corpus snippets influenced the answer (in the JSON response), so you can audit grounding.

If you want Reddit data, a safer workflow is: use Reddit's API or your own data export (or your own posts/comments), then place the text files into `backend/data/corpus/`.

---

## Quickstart

### 1) Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# build a local retrieval index from ./data/corpus/*.txt
python -m app.build_index

# run
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`.

### 2) Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Configure LLM (optional but recommended)
The app supports any **OpenAI-compatible** API endpoint.

1) Copy `.env.example` to `.env` inside `backend/`.
2) Set:
- `LLM_PROVIDER=openai_compatible`
- `OPENAI_API_KEY=...`
- `OPENAI_BASE_URL=...` (optional; defaults to OpenAI)
- `OPENAI_MODEL=...` (default: `gpt-4o-mini`)

If you do **not** set an API key, the app still runs and returns a deterministic "baseline" interpretation so the UI stays functional.

---

## Add your own "Tumblr/Reddit-style" corpus
Put plain text files here:

```
backend/data/corpus/
  tumblr_style_notes.txt
  reddit_threads_export.txt
  your_blog_posts.txt
```

Then rebuild index:

```bash
cd backend
python -m app.build_index
```

---

## API summary
- `POST /api/chart/natal` -> chart JSON (planets/houses/aspects)
- `POST /api/interpret/natal` -> interpretation JSON

---

## Repo structure

```
astro-ai-site/
  backend/
    app/
      main.py
      astrology.py
      rag.py
      llm.py
      build_index.py
      schemas.py
    data/
      corpus/
      index.json
    requirements.txt
    .env.example
  frontend/
    src/
      main.tsx
      App.tsx
      api.ts
      types.ts
    index.html
    package.json
```
