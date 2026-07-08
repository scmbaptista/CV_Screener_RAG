# routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import re

import state
import config as config
from dictionary import MainStrings as S
from rag_engine import RAGEngine
from pdf_processor import process_all_cvs

router = APIRouter()

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

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    rag = state.rag_engine
    return {
        "status": S.get("health_status"),
        "engine_ready": rag is not None,
        "indexed_documents": len(rag._indexed_files) if rag else 0
    }


@router.get("/api/config")
async def get_config_status():
    """Show which LLM providers are configured (keys are masked)."""
    or_key = config.OPENROUTER_API_KEY
    return {
        "openrouter": {
            "configured": bool(or_key),
            "key_preview": or_key[:10] + "..." if or_key and len(or_key) > 10 else ("set" if or_key else None),
            "model": config.LLM_MODEL
        },
        "mode": S.get("llm_status_full") if (or_key) else S.get("llm_status_retrieval")
    }


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics."""
    if not state.rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))
    return state.rag_engine.get_stats()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main RAG chat endpoint.

    Accepts a question, retrieves relevant CV chunks, and generates
    an LLM-based answer grounded in the CV data.
    """
    if not state.rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))

    if not request.question.strip():
        raise HTTPException(status_code=400, detail=S.get("error_400_empty"))

    try:
        result = await state.rag_engine.query(request.question)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=S.get("error_500_rag", error=str(e)))


@router.post("/api/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, force: bool = False):
    """
    Manually trigger CV ingestion.
    Set force=true to re-index all documents.
    """
    if not state.rag_engine:
        raise HTTPException(status_code=503, detail=S.get("error_503"))

    if not config.DATA_DIR.exists():
        raise HTTPException(status_code=404, detail=S.get("error_404_cv_dir", path=str(config.DATA_DIR)))

    def _ingest():
        state.rag_engine.ingest_documents(config.DATA_DIR, force_reindex=force)

    background_tasks.add_task(_ingest)

    return {
        "message": S.get("ingestion_started"),
        "directory": str(config.DATA_DIR),
        "force_reindex": force
    }


@router.get("/api/candidates", response_model=List[CandidateInfo])
async def list_candidates():
    """List all indexed candidates with basic metadata."""
    if not state.rag_engine or not config.DATA_DIR.exists():
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

frontend_dir = Path(__file__).parent.parent / "frontend"

@router.get("/")
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