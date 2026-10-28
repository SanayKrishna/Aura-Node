# Aura Node

A chat assistant for building PCs, aimed at buyers in India. You ask a question about parts, compatibility or prices, the backend runs a Google search restricted to PC retail and build sites, and Gemini answers using those results as context.

## How it works

1. The Next.js frontend sends your question to `POST /ask` on the FastAPI backend.
2. A LangChain chain runs a Google Custom Search for the question, limited to pcpartpicker.com, mdcomputers.in, vedantcomputers.com and amazon.in, and keeps the top 5 results.
3. The results and the question go into a prompt for Gemini 2.5 Pro, which writes the answer.
4. The answer is shown in the chat window.

Because every answer starts with a live search, prices and availability come from current listings instead of the model's training data.

There is also an earlier retrieval approach in the repo. `ingest.py` and `teach.py` scrape pages and store their embeddings in a Supabase vector table, and `backend/docs/` holds a motherboard manual used as source material. The current `/ask` endpoint does not use that store.

## Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, Lucide icons
- Backend: FastAPI, LangChain, Gemini (`langchain-google-genai`), Google Custom Search
- Optional: Supabase vector store for the ingest scripts

## Run it

You need Python 3.10+, Node 18+, a Gemini API key, and a Google Custom Search engine ID with its API key.

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and fill in the keys:

```env
GOOGLE_API_KEY=your-gemini-key
GOOGLE_CSE_ID=your-search-engine-id
GOOGLE_SEARCH_API_KEY=your-custom-search-key
```

```bash
uvicorn main:app --reload
```

The API runs on http://localhost:8000.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend calls the backend at `http://127.0.0.1:8000`, and the backend only accepts requests from `localhost:3000`.

## Project layout

```text
backend/
  main.py           FastAPI app and the search + Gemini chain
  ingest.py         scrapes pages into a Supabase vector store (not used by /ask)
  teach.py          adds specific pages to the same store
  check.py          lists the Gemini models your key can use
frontend/
  app/page.tsx      chat UI
```

## Notes

- LangChain is pinned to 0.3.x because the code uses imports that LangChain 1.0 removed.
- Answers are only as good as the five search results behind them, and the restricted site list leaves out a lot of reviews and benchmarks.
