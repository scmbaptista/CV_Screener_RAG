#!/usr/bin/env python3
"""
CV Screener RAG - FastAPI Backend
Main application entry point with REST API endpoints.
"""

import os
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import config
from rag_engine import RAGEngine
from pdf_processor import process_all_cvs
from strings_loader import MainStrings as S

# ───────────────────────────────────────────────
# LIFECYCLE MANAGEMENT
# ───────────────────────────────────────────────

rag_engine: Optional[RAGEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize RAG engine and ingest CVs."""
    global rag_engine
    print(S.get("startup_banner"))
    print(S.get("startup_title"))
    print("=" * 60)

    # Diagnostic: show which LLM providers are configured
    print("\n  LLM Provider Status:")
    or_key = config.OPENROUTER_API_KEY
    g_key = config.GOOGLE_API_KEY
    print(f"    OpenRouter API Key: {'✅ CONFIGURED' if or_key else '❌ NOT SET'}")
    print(f"    OpenRouter Model:   {config.LLM_MODEL}")
    print(f"    Google AI Key:      {'✅ CONFIGURED' if g_key else '❌ NOT SET'}")
    print(f"    Google Model:         {config.GOOGLE_MODEL}")
    if not or_key and not g_key:
        print(S.get("config_warning"))
        print(S.get("config_fix"))
        print(S.get("config_or"))

    rag_engine = RAGEngine()

    # Auto-ingest CVs on startup if data directory exists
    if config.DATA_DIR.exists():
        rag_engine.ingest_documents(config.DATA_DIR)
    else:
        print(f"Warning: CV directory not found at {config.DATA_DIR}")

    print(S.get("startup_ready"))
    print(S.get("startup_api_url", host=config.API_HOST, port=config.API_PORT))
    print(S.get("startup_vectorstore", path=str(config.VECTORSTORE_DIR)))
    print(S.get("startup_model", model=config.LLM_MODEL))
    print("=" * 60 + "\n")

    yield

    # Shutdown
    print(S.get("startup_shutdown"))


# ───────────────────────────────────────────────
# FASTAPI APP
# ───────────────────────────────────────────────

app = FastAPI(
    title="CV Screener RAG",
    description="AI-powered CV screening with Retrieval-Augmented Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    chunks_used: List[dict]
    query: str

class StatsResponse(BaseModel):
    total_chunks_indexed: int
    total_documents_indexed: int
    embedding_model: str
    embedding_dimension: int
    indexed_files: List[str]

class CandidateInfo(BaseModel):
    name: str
    filename: str
    role: str
    location: str
    skills: List[str]
    education: List[str]
    years_experience: int

# ───────────────────────────────────────────────
# API ENDPOINTS
# ───────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": S.get("health_status"),
        "engine_ready": rag_engine is not None,
        "indexed_documents": len(rag_engine._indexed_files) if rag_engine else 0
    }


@app.get("/api/config")
async def get_config_status():
    """Show which LLM providers are configured (keys are masked)."""
    or_key = config.OPENROUTER_API_KEY
    g_key = config.GOOGLE_API_KEY
    return {
        "openrouter": {
            "configured": bool(or_key),
            "key_preview": or_key[:10] + "..." if or_key and len(or_key) > 10 else ("set" if or_key else None),
            "model": config.LLM_MODEL
        },
        "google_ai": {
            "configured": bool(g_key),
            "key_preview": g_key[:10] + "..." if g_key and len(g_key) > 10 else ("set" if g_key else None),
            "model": config.GOOGLE_MODEL
        },
        "mode": S.get("llm_status_full") if (or_key or g_key) else S.get("llm_status_retrieval")
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics."""
    if not rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))
    return rag_engine.get_stats()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main RAG chat endpoint.

    Accepts a question, retrieves relevant CV chunks, and generates
    an LLM-based answer grounded in the CV data.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))

    if not request.question.strip():
        raise HTTPException(status_code=400, detail=S.get("error_400_empty"))

    try:
        result = await rag_engine.query(request.question)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=S.get("error_500_rag", error=str(e)))


@app.post("/api/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, force: bool = False):
    """
    Manually trigger CV ingestion.
    Set force=true to re-index all documents.
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))

    if not config.DATA_DIR.exists():
        raise HTTPException(status_code=404, detail=S.get("error_404_cv_dir", path=str(config.DATA_DIR)))

    def _ingest():
        rag_engine.ingest_documents(config.DATA_DIR, force_reindex=force)

    background_tasks.add_task(_ingest)

    return {
        "message": S.get("ingestion_started"),
        "directory": str(config.DATA_DIR),
        "force_reindex": force
    }


@app.get("/api/candidates", response_model=List[CandidateInfo])
async def list_candidates():
    """List all indexed candidates with basic metadata."""
    if not rag_engine or not config.DATA_DIR.exists():
        return []

    try:
        docs = process_all_cvs(config.DATA_DIR)
        candidates = []
        for doc in docs:
            # Extract basic info from parsed document
            sections = doc.sections

            # Try to infer role from summary or first experience
            role = "Unknown"
            if "PROFESSIONAL SUMMARY" in sections:
                summary = sections["PROFESSIONAL SUMMARY"]
                # Simple heuristic: look for common role words
                for r in ["Developer", "Engineer", "Manager", "Designer", "Scientist", "Architect", "Analyst", "Lead"]:
                    if r.lower() in summary.lower():
                        role = summary.split(r)[0].split()[-3:]  # rough extraction
                        role = " ".join(role) + r if role else r
                        break

            # Extract skills
            skills = []
            if "SKILLS" in sections:
                skills_text = sections["SKILLS"]
                skills = [s.strip() for s in skills_text.split("•") if s.strip()][:10]

            # Extract education institutions
            education = []
            if "EDUCATION" in sections:
                edu_text = sections["EDUCATION"]
                # Look for university abbreviations in parentheses
                import re
                matches = re.findall(r'\(([^)]+)\)', edu_text)
                education = matches[:3]

            candidates.append(CandidateInfo(
                name=doc.candidate_name,
                filename=doc.filename,
                role=role if isinstance(role, str) else "Full-Stack Developer",
                location="",
                skills=skills,
                education=education,
                years_experience=0
            ))

        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=S.get("error_500_candidates", error=str(e)))


# ───────────────────────────────────────────────
# FRONTEND SERVING
# ───────────────────────────────────────────────

# Serve static frontend files (HTML, JS, CSS)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({
        "message": "CV Screener RAG API is running",
        "docs": "/docs",
        "health": "/health"
    })


# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )
