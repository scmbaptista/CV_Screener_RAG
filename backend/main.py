# main.py
#!/usr/bin/env python3
"""
CV Screener RAG - FastAPI Backend
Main application entry point with REST API endpoints.
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config as config
from dictionary import MainStrings as S
from rag_engine import RAGEngine
import state
from routes import router

# ───────────────────────────────────────────────
# LIFECYCLE MANAGEMENT
# ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize RAG engine and ingest CVs."""
    print(S.get("startup_banner"))
    print(S.get("startup_title"))
    print("=" * 60)

    # Diagnostic: show which LLM providers are configured
    print("\n  LLM Provider Status:")
    or_key = config.OPENROUTER_API_KEY
    print(f"    OpenRouter API Key: {'✅ CONFIGURED' if or_key else '❌ NOT SET'}")
    print(f"    OpenRouter Model:   {config.LLM_MODEL}")    
    print(S.get("config_warning"))
    print(S.get("config_fix"))

    state.rag_engine = RAGEngine()

    # Auto-ingest CVs on startup if data directory exists
    if config.DATA_DIR.exists():
        state.rag_engine.ingest_documents(config.DATA_DIR)
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

# Include all routes from the controller
app.include_router(router)

# Serve static frontend files (HTML, JS, CSS)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


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