# CV Screener RAG — Architecture & Implementation Documentation

> **Leadtech Full-Stack AI Engineer Technical Task**  
> **Author:** AI Engineer (Technical Assessment)  
> **Date:** July 2026  
> **Version:** 1.0.0  
> **Status:** Complete — All requirements implemented

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Component Diagram](#3-component-diagram)
4. [Data Flow](#4-data-flow)
5. [Technology Stack & Rationale](#5-technology-stack--rationale)
6. [What Was Implemented](#6-what-was-implemented)
7. [API Endpoints](#7-api-endpoints)
8. [Project Structure](#8-project-structure)
9. [Security & Privacy](#9-security--privacy)
10. [Scalability Path](#10-scalability-path)
11. [Evaluation Criteria Mapping](#11-evaluation-criteria-mapping)

---

## 1. Executive Summary

This document describes the complete architecture and implementation of the **CV Screener RAG** — an AI-powered recruitment assistant built as a technical prototype for the Leadtech Full-Stack AI Engineer position. The system implements a **Retrieval-Augmented Generation (RAG)** pipeline over a synthetic dataset of 30 CVs, enabling natural-language queries with grounded, sourced answers.

### Key Capabilities

- **Chat Interface:** Ask questions about candidates in natural language
- **Semantic Search:** Find relevant CV chunks using vector embeddings
- **LLM Generation:** Synthesize answers with source attribution
- **Relevance Filtering:** Prevent false positives with strict keyword validation
- **Privacy-Safe:** All 30 CVs are synthetically generated — zero real personal data

### Architecture Highlights

- **Modular design:** Separate modules for data generation, PDF processing, RAG engine, and API
- **Local-first:** Embeddings run on CPU (MiniLM), vector store is persistent (ChromaDB)
- **Cloud LLM fallback:** OpenRouter with Google AI Studio as secondary provider
- **Zero-build frontend:** Vanilla HTML/CSS/JS — single files, no npm/webpack
- **Centralized strings:** All UI text and prompts in `data/strings.json` for easy localization

---

## 2. System Architecture Overview

The system follows a **layered, modular architecture** with clear separation of concerns across five layers: Data, Ingestion, Retrieval, Generation, and Presentation. Each layer is independent and swappable, allowing for easy extension and maintenance.

### Layer 1 — Data Layer

- Synthetic CV generation (30 PDFs) with Faker + ReportLab
- All generation data stored in editable JSON files (`data/cv_data.json`)
- Deterministic avatars with initials (privacy-safe)

### Layer 2 — Ingestion Layer

- PDF text extraction via `pdfplumber` (layout-preserving)
- Section-aware parsing (Summary, Experience, Education, Skills, etc.)
- Contextualized chunking: `[Name] [Section]` + content
- Embedding generation with `all-MiniLM-L6-v2` (384-dim, local CPU)
- Persistent vector storage in ChromaDB (cosine similarity)

### Layer 3 — Retrieval Layer

- Query embedding with same model as ingestion (consistency)
- ChromaDB semantic search (top-K chunks)
- Strict keyword-based relevance filtering (prevents false positives)

### Layer 4 — Generation Layer

- System prompt enforcing grounding-only policy
- Context injection into user prompt
- OpenRouter LLM API (auto-routing free models)
- Google AI Studio fallback (Gemini)
- Retrieval-only fallback if all LLMs fail

### Layer 5 — Presentation Layer

- FastAPI REST backend with async endpoints
- Vanilla HTML/CSS/JS frontend (zero build step)
- Real-time chat with source citation badges
- Responsive design with example question panel

---

## 3. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Frontend (index.html + chat.js + chat.css)                     │   │
│  │  • Chat Input  • Message Display  • Source Badges  • Examples   │   │
│  └────────────────────────────────┬─────────────────────────────────┘   │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ HTTP/JSON
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            API LAYER (FastAPI)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ /api/chat  │  │ /api/stats │  │ /api/ingest│  │ /api/config    │   │
│  │ (async)    │  │ (metrics)  │  │ (re-index) │  │ (diagnostics)  │   │
│  └─────┬──────┘  └────────────┘  └────────────┘  └────────────────┘   │
└────────┼──────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CORE ENGINE (RAGEngine)                        │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐  │
│  │  INGESTION PIPELINE│  │  RETRIEVAL PIPELINE│  │  GENERATION    │  │
│  │  PDF → Text →      │  │  Query → Embed →   │  │  Prompt + LLM  │  │
│  │  Sections → Chunks │  │  ChromaDB → Filter │  │  + Sources     │  │
│  │  → Embed → Store   │  │  → Top-K Relevant  │  │                │  │
│  └────────────────────┘  └────────────────────┘  └────────────────┘  │
└──────────────────────────┬─────────────────────────────────────────────┘
           │               │               │
           ▼               ▼               ▼
┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐
│   ChromaDB     │  │  Sentence      │  │   OpenRouter /      │
│  (Vector Store)│  │  Transformers  │  │   Google AI Studio  │
│  Persistent    │  │  all-MiniLM    │  │   (Cloud LLM)       │
│  Cosine sim    │  │  384-dim, CPU  │  │   Free tier         │
└────────────────┘  └────────────────┘  └─────────────────────┘
```

> **Figure 1:** High-level component architecture showing the five layers and their interactions. The Frontend communicates with the FastAPI backend, which orchestrates the RAG Engine. The engine interacts with three external services: ChromaDB (vector storage), SentenceTransformers (local embeddings), and OpenRouter/Google AI Studio (cloud LLM inference).

---

## 4. Data Flow

The system operates through two primary data flows: **Ingestion** (preparation) and **Query** (runtime). Both flows are fully automated and require no manual intervention after initial setup.

### 4.1 Ingestion Flow

| Step | Action | Output |
|------|--------|--------|
| 1 | **CV Generation** — Faker (seed=42) → Candidate data | PDF with avatar, sections, skills |
| 2 | **Text Extraction** — PDF → pdfplumber | Raw text (layout preserved) |
| 3 | **Section Detection** — Regex patterns | `{SUMMARY: "...", EXPERIENCE: "...", ...}` |
| 4 | **Contextualized Chunking** | `[Mark Johnson] [WORK EXPERIENCE]
Led development of...` |
| 5 | **Embedding** — all-MiniLM-L6-v2 | Vector[384] |
| 6 | **Vector Storage** — ChromaDB | Persistent HNSW index (cosine similarity) |

### 4.2 Query Flow

| Step | Action | Output |
|------|--------|--------|
| 1 | **User Input** | `"Who has Python and AWS experience?"` |
| 2 | **Query Embedding** — all-MiniLM-L6-v2 | Query Vector[384] |
| 3 | **Semantic Retrieval** — ChromaDB | Top-15 chunks (cosine similarity) |
| 4 | **Relevance Filtering** | Keyword containment check → Score = matched/total |
| 5 | **Prompt Construction** | System Prompt + User Prompt (context + question) |
| 6 | **LLM Generation** | OpenRouter → Google AI Studio → Retrieval-only |
| 7 | **Response Formatting** | Answer text + Source badges + Relevance scores |

---

## 5. Technology Stack & Rationale

Each technology was chosen based on a balance of capability, simplicity, and suitability for a prototype. The goal was a working product, not an over-engineered solution.

| Layer | Technology | Purpose | Rationale |
|-------|-----------|---------|-----------|
| CV Generation | ReportLab + Pillow + Faker | Programmatic PDF creation | Deterministic, privacy-safe, professional layout |
| PDF Parsing | pdfplumber | Text extraction | Better layout preservation than PyPDF2 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Semantic vectors | 384-dim, ~80MB, CPU-only, no API costs |
| Vector DB | ChromaDB | Persistent storage | Zero-config, Python-native, HNSW indexing |
| LLM | OpenRouter (openrouter/free) | Cloud inference | Free tier, auto-routing, no local GPU needed |
| LLM Fallback | Google AI Studio (Gemini) | Secondary provider | Also free, higher rate limits |
| Backend | FastAPI + Uvicorn | REST API | Async, auto-docs, Pydantic validation |
| Frontend | Vanilla HTML/CSS/JS | Chat UI | Zero build step, maximum portability |
| Data | JSON files | Configuration | Editable without touching code |

---

## 6. What Was Implemented

### 6.1 Synthetic CV Generator (`generate_cvs.py`)

Generates 30 unique, realistic CVs in PDF format. All data is loaded from **`data/cv_data.json`**, allowing customization without code changes. Each CV includes: AI-generated avatar (colored circle with initials), contact info, professional summary, 2-5 work experiences, 1-2 education entries, 8-18 skills, languages, and optional certifications. The Faker library uses `seed=42` for full reproducibility.

### 6.2 PDF Processor (`pdf_processor.py`)

Extracts text using `pdfplumber` (superior to PyPDF2 for layout preservation). Detects CV sections via regex patterns: Professional Summary, Work Experience, Education, Skills, Languages, Certifications, Projects, Awards. Returns structured `CVDocument` objects with raw text, section dictionary, and metadata. Preserving section boundaries is critical for RAG quality — blind chunking would split job descriptions in half, losing semantic coherence.

### 6.3 RAG Engine (`rag_engine.py`)

The core of the system. Implements three pipelines:

**Ingestion:** Sentence-aware chunking (512 words, 64 overlap) with contextualized prefixes (`[Name] [Section]`). This dramatically improves retrieval because the embedding encodes WHO and WHAT SECTION the information belongs to. `all-MiniLM-L6-v2` generates 384-dim vectors stored in ChromaDB with cosine similarity.

**Retrieval:** Query embedding → ChromaDB top-15 search → strict keyword filtering (score = matched_keywords / total_keywords). Chunks with 0 matches are discarded. This prevents false positives like "diabetes" matching "node.js" via fuzzy character matching.

**Generation:** System prompt enforces grounding-only policy. Three LLM providers are tried in order: OpenRouter (primary), Google AI Studio (fallback), retrieval-only (ultimate fallback). Source candidates are extracted from chunk metadata and returned with every answer.

### 6.4 FastAPI Backend (`main.py`)

REST API with endpoints:

- `GET /` — Serve chat frontend
- `POST /api/chat` — Main RAG query (async)
- `GET /api/stats` — Vector store statistics
- `POST /api/ingest` — Trigger CV re-indexing
- `GET /api/candidates` — Parsed candidate metadata
- `GET /api/config` — LLM provider diagnostics
- `GET /health` — Status check
- `GET /docs` — Swagger UI (auto-generated)

On startup, automatically ingests new CVs and prints diagnostic information about configured LLM providers.

### 6.5 Chat Frontend (`index.html` + `chat.js` + `chat.css`)

Zero-build, single-page interface with:

- Real-time messaging
- Source citation badges
- Example question panel
- Auto-resizing textarea
- Loading indicator with animated dots
- Error toast notifications
- Responsive design (sidebar hides on mobile)

All JavaScript and CSS are in separate files for cacheability and maintainability.

### 6.6 Strings Management (`strings_loader.py` + `data/strings.json`)

All UI text, prompts, log messages, and error messages are centralized in `data/strings.json`. The `strings_loader.py` module provides cached loading with format string support. This enables easy customization and future localization (i18n) without touching Python code.

---

## 7. API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Serve chat frontend | None |
| `POST` | `/api/chat` | Main RAG query (async) | None |
| `GET` | `/api/stats` | Vector store statistics | None |
| `POST` | `/api/ingest` | Trigger CV re-indexing | None |
| `GET` | `/api/candidates` | Parsed candidate metadata | None |
| `GET` | `/api/config` | LLM provider diagnostics | None |
| `GET` | `/health` | Health check | None |
| `GET` | `/docs` | Swagger UI (auto-generated) | None |

---

## 8. Project Structure

```
cv-screener-rag/
├── README.md                          Project overview & quick start
├── generate_cvs.py                   Synthetic CV generator (reads data/cv_data.json)
├── requirements.txt                  Python dependencies
├── start.sh                          One-command startup script
├── .env.example                      Configuration template
│
├── backend/
│   ├── main.py                       FastAPI application & REST endpoints
│   ├── rag_engine.py                 Core RAG pipeline (ingest → retrieve → generate)
│   ├── pdf_processor.py              PDF extraction & section parsing
│   ├── config.py                     Centralized environment configuration
│   └── strings_loader.py             String loading & localization module
│
├── frontend/
│   ├── index.html                    Chat UI (HTML only)
│   ├── chat.js                       Chat logic (separate from HTML)
│   └── chat.css                      Chat styles (separate from HTML)
│
├── data/
│   ├── cvs/                          Generated synthetic CVs (30 PDFs)
│   ├── cv_data.json                  All CV generation data (editable)
│   └── strings.json                  All UI/text strings (editable)
│
├── docs/
│   ├── ARCHITECTURE.md               Deep-dive technical architecture
│   └── Project_Architecture_Documentation.md  This document
│
└── vectorstore/                      ChromaDB persistent storage (created at runtime)
```

---

## 9. Security & Privacy

Security and privacy were considered at every layer of the architecture.

| Concern | Mitigation |
|---------|-----------|
| Prompt injection | System prompt explicitly forbids answering from outside provided context |
| Hallucination | LLM instructed to say "I don't have that information" if context is insufficient |
| Data leakage | All CVs are synthetic — zero real PII used anywhere |
| API key exposure | `.env` file excluded from git via `.gitignore` |
| File traversal | PDF processing restricted to `data/cvs/` directory via `Path.glob()` |
| False positives | Strict keyword filtering prevents irrelevant chunks from reaching LLM |
| Rate limiting | Multiple LLM providers with automatic fallback chain |

---

## 10. Scalability Path

While this is a prototype, the architecture supports scaling in multiple directions.

| Bottleneck | Current | Scale Path |
|-----------|---------|-----------|
| Single machine | Local ChromaDB | Deploy ChromaDB as server, use Redis caching |
| LLM latency | Synchronous calls | Add SSE streaming, use faster models |
| Concurrent users | Single worker | Add request queue, use gunicorn workers |
| Larger corpus | Local ChromaDB | Migrate to PostgreSQL + pgvector or Pinecone |
| Multi-tenant | Single collection | Add collection-per-tenant isolation |
| Better retrieval | Basic semantic | Hybrid search (BM25 + semantic), re-ranking |

---

## 11. Evaluation Criteria Mapping

This section maps the Leadtech evaluation criteria directly to implemented features and design decisions.

| Criterion | How This Project Responds | Evidence |
|-----------|--------------------------|----------|
| **Execution & Functionality** | End-to-end RAG pipeline works: generates CVs, indexes them, answers queries with sources | 30 CVs generated, 203 chunks indexed, chat returns grounded answers |
| **Thought Process** | Documented architecture decisions in ARCHITECTURE.md and this document | Why ChromaDB, why MiniLM, why manual RAG, why vanilla JS |
| **Code Quality** | Modular structure, type hints, docstrings, error handling, configuration management | 5 backend modules, 3 frontend files, `.env` config, `strings.json` |
| **Creativity & Ingenuity** | Contextualized chunking, strict relevance filtering, triple LLM fallback chain | `[Name] [Section]` prefixes, keyword-only scoring, OpenRouter→Google→retrieval fallback |
| **AI Literacy** | Awareness of embeddings, HNSW, prompt engineering, grounding, RAG limitations | MiniLM for embeddings, system prompt rules, fallback modes, relevance validation |
| **Learn & Adapt** | Iterated on bugs: regex JS issues, false positives, 429 rate limits, telemetry warnings | Fixed regex with split/join, removed SequenceMatcher, added Google fallback, suppressed warnings |

---

## Conclusion

This project demonstrates full-stack AI engineering capability: from data generation to vector search to LLM integration to UI. The system is privacy-safe, reproducible, and extensible. All requirements from the Leadtech business case have been implemented, with additional features including relevance filtering, triple LLM fallback, centralized string management, and comprehensive documentation.
