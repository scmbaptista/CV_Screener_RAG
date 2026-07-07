# CV Screener RAG — AI-Powered CV Screening Prototype

> **End-to-end RAG prototype for screening résumés using semantic search + LLM generation.**
> Built for the Leadtech Full-Stack AI Engineer technical assessment.

---

## 🎯 What This Is

This project is a complete, working prototype of an **AI-powered CV screening tool** that lets you ask natural-language questions about a pool of candidates and get grounded, sourced answers.

**Example questions you can ask:**
- *"Who has experience with Python and Kubernetes?"*
- *"Which candidate graduated from UPC?"*
- *"Summarize the profile of Jane Doe"*
- *"Find backend engineers with 5+ years of cloud experience"*
- *"Which candidates speak German fluently?"*

All answers are **grounded strictly in the CV database** — the system retrieves relevant document chunks via semantic search and feeds them to an LLM with explicit instructions not to hallucinate.

---

## 🏗️ Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  Chat Interface (HTML/CSS/JS) — Single-page, no build step          │  │
│  │  • Question input  • Source citations  • Example prompts            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ HTTP/JSON
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  /api/chat      │  │  /api/stats     │  │  /api/ingest            │   │
│  │  RAG endpoint   │  │  Vector store   │  │  Re-index CVs           │   │
│  │  (async)        │  │  metrics        │  │  (background task)      │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    RAG ENGINE (rag_engine.py)                       │ │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │ │
│  │  │  Ingestion   │───►│  Retrieval   │───►│  Generation (LLM)    │   │ │
│  │  │  Pipeline    │    │  (Semantic)  │    │  + Source Tracking   │   │ │
│  │  └──────────────┘    └──────────────┘    └──────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   ChromaDB      │    │ SentenceTransformers│    │   OpenRouter LLM    │
│  (Vector Store) │    │   (Embeddings)      │    │  (mistral-7b-free)  │
│  Persistent     │    │  all-MiniLM-L6-v2   │    │  Cloud API          │
│  Cosine sim     │    │  384-dim, local     │    │  No local GPU needed│
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 📁 Project Structure

```
cv-screener-rag/
├── generate_cvs.py              # Synthetic CV dataset generator (30 PDFs)
├── requirements.txt             # Python dependencies
├── start.sh                     # One-command startup script
├── .env.example                 # Configuration template
│
├── backend/
│   ├── main.py                  # FastAPI app & REST endpoints
│   ├── rag_engine.py            # Core RAG pipeline (ingest → retrieve → generate)
│   ├── pdf_processor.py         # PDF text extraction + section parsing
│   └── config.py                # Centralized configuration
│
├── frontend/
│   └── index.html               # Single-page chat UI (no build step)
│
├── data/cvs/                    # Generated synthetic CVs (PDFs)
├── vectorstore/                 # ChromaDB persistent storage
│
└── docs/
    ├── ARCHITECTURE.md          # Deep-dive architecture documentation
    └── WHAT_WAS_DONE.md         # Implementation details & design decisions
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- ~2GB free disk space (for models + vector store)

### 2. Setup

```bash
# Clone / navigate to project
cd cv-screener-rag

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key (free at openrouter.ai)
```

### 3. Generate CVs & Start

```bash
# Option A: Use the startup script
chmod +x start.sh
./start.sh

# Option B: Manual steps
python3 generate_cvs.py          # Creates 30 synthetic PDFs
cd backend && python3 -m uvicorn main:app --reload
```

### 4. Use
Open your browser at **http://localhost:8000**

---

## 🔑 API Key (Free)

The system uses **OpenRouter** for LLM inference, which offers free tiers for many models:

1. Go to [https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
2. Create a free API key
3. Paste it in `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
   ```

**No credit card required.** The default model (`openrouter/free`) runs on the free tier.

> **Fallback:** If no API key is provided, the system still works in "retrieval-only mode" — it returns the most relevant raw CV excerpts instead of synthesized answers.

---

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the chat frontend |
| `POST` | `/api/chat` | Main RAG query endpoint |
| `GET` | `/api/stats` | Vector store statistics |
| `POST` | `/api/ingest` | Trigger CV re-ingestion |
| `GET` | `/api/candidates` | List all parsed candidates |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Auto-generated Swagger UI |

### Example API Call
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Who has Python experience?", "top_k": 5}'
```

---

## 🛡️ Privacy & Ethics

**All CVs are synthetically generated.** No real personal data, names, or photographs of actual people are used. The dataset is:
- ✅ Fully reproducible (`Faker` + fixed seed)
- ✅ Privacy-safe by design
- ✅ Diverse in roles, skills, and backgrounds
- ✅ Includes realistic structure (photos, experience, education, skills)

---

## 📊 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Vanilla HTML/CSS/JS | Zero-build chat UI |
| **Backend** | FastAPI + Uvicorn | Async REST API |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | Local, 384-dim vectors |
| **Vector DB** | ChromaDB | Persistent semantic search |
| **LLM** | OpenRouter (Mistral 7B) | Cloud inference, free tier |
| **PDF Gen** | ReportLab + Pillow | Synthetic CV generation |
| **PDF Parse** | pdfplumber | High-quality text extraction |

---

## 📄 License

This project was created as a technical assessment prototype. All synthetic data and code are provided as-is for demonstration purposes.
