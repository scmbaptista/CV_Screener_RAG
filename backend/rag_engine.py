"""
RAG Engine Module
Core retrieval-augmented generation pipeline for the CV Screener.
"""

import json
import re
import httpx
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Suppress ALL warnings BEFORE importing chromadb
import warnings
warnings.filterwarnings("ignore")
import logging
for logger_name in ["chromadb", "chromadb.telemetry", "chromadb.telemetry.product", "chromadb.config", "chromadb.segment", "chromadb.ingest"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).propagate = False
    logging.getLogger(logger_name).handlers = []

# Now safe to import chromadb
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from pdf_processor import CVDocument, process_all_cvs
import config
from dictionary import RAGStrings as S


class Chunk:
    """Represents a text chunk with metadata."""
    def __init__(self, text: str, source_file: str, candidate_name: str, section: str, chunk_index: int, total_chunks: int):
        self.text = text
        self.source_file = source_file
        self.candidate_name = candidate_name
        self.section = section
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.id = f"{source_file}_{section}_{chunk_index}"


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine for CV Screening.

    Responsibilities:
    - Document ingestion and chunking
    - Vector storage and semantic retrieval
    - LLM-based answer generation with source grounding
    - Relevance validation to prevent hallucinated/false-positive matches
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(config.VECTORSTORE_DIR)
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="cv_collection",
            metadata={"hnsw:space": "cosine"}
        )

        self._indexed_files: set = set()
        self._load_index_state()

    def _load_index_state(self):
        """Load the set of already indexed files to avoid re-processing."""
        state_file = config.VECTORSTORE_DIR / "index_state.json"
        if state_file.exists():
            with open(state_file) as f:
                self._indexed_files = set(json.load(f))

    def _save_index_state(self):
        """Persist the index state."""
        state_file = config.VECTORSTORE_DIR / "index_state.json"
        with open(state_file, "w") as f:
            json.dump(list(self._indexed_files), f)

    # -------------------------------------------------
    # INGESTION PIPELINE
    # -------------------------------------------------

    def _chunk_text(self, text: str, chunk_size: int = config.CHUNK_SIZE,
                    overlap: int = config.CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks by words.
        Preserves sentence boundaries where possible.
        """
        sentences = text.replace("\n", " ").split(". ")
        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()

            if current_len + len(words) <= chunk_size:
                current_chunk.append(sentence)
                current_len += len(words)
            else:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    s_words = len(s.split())
                    if overlap_len + s_words <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += s_words
                    else:
                        break
                current_chunk = overlap_sentences + [sentence]
                current_len = overlap_len + len(words)

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        return chunks

    def _create_chunks_from_document(self, doc: CVDocument) -> List[Chunk]:
        """Create intelligent chunks from a CV document, preserving sections."""
        all_chunks = []

        for section_name, section_text in doc.sections.items():
            if len(section_text.split()) < 20:
                # Short section, keep as single chunk
                section_chunks = [section_text]
            else:
                section_chunks = self._chunk_text(section_text)

            for idx, chunk_text in enumerate(section_chunks):
                # Prepend section context to each chunk for better retrieval
                contextualized = f"[{doc.candidate_name}] [{section_name}]\n{chunk_text}"
                chunk = Chunk(
                    text=contextualized,
                    source_file=doc.filename,
                    candidate_name=doc.candidate_name,
                    section=section_name,
                    chunk_index=idx,
                    total_chunks=len(section_chunks)
                )
                all_chunks.append(chunk)

        return all_chunks

    def ingest_documents(self, cv_dir: Path, force_reindex: bool = False):
        """
        Ingest all CV PDFs from a directory into the vector store.

        Args:
            cv_dir: Path to directory containing CV PDFs
            force_reindex: If True, re-index all documents even if already indexed
        """
        if force_reindex:
            self.collection.delete(where={})
            self._indexed_files.clear()

        documents = process_all_cvs(cv_dir)
        new_docs = [d for d in documents if d.filename not in self._indexed_files]

        if not new_docs:
            print(S.get("log_no_new_docs"))
            return

        print(S.get("log_indexing", count=len(new_docs)))

        for doc in new_docs:
            chunks = self._create_chunks_from_document(doc)
            if not chunks:
                continue

            # Generate embeddings
            texts = [c.text for c in chunks]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False).tolist()

            # Prepare ChromaDB batch
            ids = [c.id for c in chunks]
            metadatas = [{
                "source_file": c.source_file,
                "candidate_name": c.candidate_name,
                "section": c.section,
                "chunk_index": c.chunk_index,
                "total_chunks": c.total_chunks
            } for c in chunks]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            self._indexed_files.add(doc.filename)
            print(S.get("log_indexed", chunks=len(chunks), name=doc.candidate_name))

        self._save_index_state()
        print(S.get("log_index_complete") + f" {len(self._indexed_files)}")

    # -------------------------------------------------
    # RELEVANCE VALIDATION
    # -------------------------------------------------

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from a query, filtering stop words."""
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "and", "but", "or", "yet", "so",
            "if", "because", "although", "though", "while", "where", "when",
            "that", "which", "who", "whom", "whose", "what", "this", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
            "her", "us", "them", "my", "your", "his", "her", "its", "our", "their",
            "mine", "yours", "hers", "ours", "theirs", "who", "which", "whom",
            "whose", "what", "find", "list", "show", "tell", "give", "get",
            "search", "look", "any", "all", "some", "one", "two", "three",
            "first", "last", "most", "more", "many", "much", "few", "little",
            "other", "another", "such", "only", "own", "same", "so", "than",
            "too", "very", "just", "now", "then", "here", "there", "also",
            "back", "still", "even", "well", "how", "why", "where", "when",
            "about", "up", "out", "down", "off", "over", "again", "further",
            "once", "does", "did", "doing", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "than", "too", "very", "just", "don", "should", "now"
        }

        # Remove punctuation and split
        cleaned = re.sub(r"[^\w\s]", " ", query.lower())
        words = [w for w in cleaned.split() if len(w) > 2 and w not in stop_words]
        return words

    def _chunk_relevance_score(self, query: str, chunk_text: str) -> float:
        """
        Score how relevant a chunk is to the query.
        Returns 0.0-1.0 where 1.0 = exact match, 0.0 = no relation.

        STRICT policy: if no keyword from the query appears in the chunk,
        the score is 0.0. No fuzzy character matching (which produces
        false positives like 'diabetes' matching 'node.js.' via SequenceMatcher).
        """
        query_lower = query.lower().strip()
        chunk_lower = chunk_text.lower()

        # 1. Exact phrase match
        if query_lower in chunk_lower:
            return 1.0

        # 2. Keyword containment (STRICT - no fuzzy fallback)
        keywords = self._extract_keywords(query)
        if not keywords:
            return 0.0

        matches = sum(1 for kw in keywords if kw in chunk_lower)
        if matches == 0:
            return 0.0  # STRICT: no keyword found = not relevant

        keyword_ratio = matches / len(keywords)
        return keyword_ratio

    def _filter_relevant_chunks(self, query: str, chunks: List[Dict[str, Any]],
                                min_score: float = 0.01) -> List[Dict[str, Any]]:
        """
        Filter retrieved chunks to only those actually relevant to the query.
        Prevents false positives like "diabetes" matching random skill lists.
        """
        filtered = []
        for chunk in chunks:
            text = chunk["text"]
            # Remove the contextual prefix for cleaner matching
            clean_text = text.split("\n", 1)[1] if "\n" in text else text

            relevance = self._chunk_relevance_score(query, clean_text)
            chunk["relevance_score"] = relevance

            if relevance >= min_score:
                filtered.append(chunk)

        # Sort by relevance descending
        filtered.sort(key=lambda c: c["relevance_score"], reverse=True)
        return filtered

    # -------------------------------------------------
    # RETRIEVAL PIPELINE
    # -------------------------------------------------

    def retrieve(self, query: str, top_k: int = config.TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a given query.

        Args:
            query: User question
            top_k: Number of chunks to retrieve

        Returns:
            List of chunk dictionaries with text and metadata
        """
        query_embedding = self.embedding_model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k * 3,  # Retrieve more to allow filtering
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        # Filter to only actually relevant chunks
        return self._filter_relevant_chunks(query, chunks)

    # -------------------------------------------------
    # GENERATION PIPELINE
    # -------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return S.get("system_prompt")

    def _build_user_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Build the user prompt with retrieved context."""

        # Deduplicate and format context
        seen_candidates = set()
        context_parts = []

        for chunk in context_chunks:
            meta = chunk["metadata"]
            candidate = meta["candidate_name"]
            section = meta["section"]
            text = chunk["text"]

            # Remove the contextual prefix we added during chunking for cleaner display
            clean_text = text.split("\n", 1)[1] if "\n" in text else text

            context_parts.append(f"--- FROM: {candidate} | SECTION: {section} ---\n{clean_text}")
            seen_candidates.add(candidate)

        context_str = "\n\n".join(context_parts)

        return S.get("user_prompt_template", context=context_str, query=query)

    async def _call_openrouter(self, messages: List[dict]) -> str:
        """Call OpenRouter API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{config.OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "CV-Screener-RAG"
                },
                json={
                    "model": config.LLM_MODEL,
                    "messages": messages,
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": config.LLM_MAX_TOKENS
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Generate an answer using the LLM with retrieved context.
        Tries OpenRouter first, then Google AI Studio as fallback.

        Returns:
            Tuple of (answer_text, list_of_source_candidates)
        """
        # If no relevant chunks found, return immediately
        if not context_chunks:
            return (
                S.get("not_found_answer_no_context"),
                []
            )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, context_chunks)

        # Try OpenRouter first
        if config.OPENROUTER_API_KEY:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            try:
                answer = await self._call_openrouter(messages)
                sources = list(set(chunk["metadata"]["candidate_name"] for chunk in context_chunks))
                return answer, sources
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 404:
                    error_msg = (
                        "[LLM Error: Model not found (404)]\n\n"
                        f"The model '{config.LLM_MODEL}' is not available on OpenRouter.\n"
                        "This usually means the free model was removed or renamed.\n\n"
                        "To fix this:\n"
                        "1. Visit https://openrouter.ai/models and filter by 'Free'\n"
                        "2. Pick a working model (e.g., meta-llama/llama-3.3-70b-instruct:free)\n"
                        "3. Update LLM_MODEL in your .env file\n\n"
                        "Meanwhile, here is the retrieval-only result:"
                    )
                    print(f"OpenRouter 404: Model '{config.LLM_MODEL}' not found. Check openrouter.ai/models for current free models.")
                    fb_answer, sources = self._fallback_answer(query, context_chunks)
                    return error_msg + "\n\n" + fb_answer, sources
                elif status == 401:
                    error_msg = "[LLM Error: Invalid API key (401)] — Check your OPENROUTER_API_KEY in .env"
                    print("OpenRouter 401: Invalid API key")
                    fb_answer, sources = self._fallback_answer(query, context_chunks)
                    return error_msg + "\n\n" + fb_answer, sources
                elif status == 429:
                    error_msg = (
                        "[LLM Error: Rate limit exceeded (429)]\n\n"
                        "The OpenRouter free tier allows 50 requests per day.\n"
                        "You have reached this limit.\n\n"
                        "Solutions:\n"
                        "1. Wait until tomorrow for the daily reset, OR\n"
                        "2. Add $10 of credits to OpenRouter (raises limit to 1000/day forever), OR\n"
                        "3. Use the system without LLM — retrieval-only works perfectly\n\n"
                        "Meanwhile, here is the retrieval-only result:"
                    )
                    print("OpenRouter 429: Rate limit hit (free tier = 50 requests/day).")
                    fb_answer, sources = self._fallback_answer(query, context_chunks)
                    return error_msg + "\n\n" + fb_answer, sources
                else:
                    print(f"OpenRouter error {status}: {e.response.text[:200]}")
                    # Fall through to next provider
            except Exception as e:
                print(f"OpenRouter unexpected error: {e}. Trying fallback...")
                # Fall through to next provider

        # Ultimate fallback: retrieval-only
        print("All LLM providers failed. Using retrieval-only fallback.")
        return self._fallback_answer(query, context_chunks)

    def _fallback_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Generate a simple retrieval-only answer when LLM is unavailable."""
        sources = list(set(chunk["metadata"]["candidate_name"] for chunk in context_chunks))

        answer_parts = [S.get("fallback_header")]

        for chunk in context_chunks:
            meta = chunk["metadata"]
            text = chunk["text"].split("\n", 1)[1] if "\n" in chunk["text"] else chunk["text"]
            answer_parts.append(f"\n**{meta['candidate_name']}** ({meta['section']}):")
            answer_parts.append(text[:300] + "..." if len(text) > 300 else text)

        answer_parts.append(f"\n\n*Sources: {', '.join(sources)}*")
        return "\n".join(answer_parts), sources

    # -------------------------------------------------
    # FULL RAG QUERY
    # -------------------------------------------------

    async def query(self, question: str) -> Dict[str, Any]:
        """
        End-to-end RAG query: retrieve + generate.

        Returns:
            Dict with keys: answer, sources, chunks_used, query
        """
        print(S.get("log_query_prefix") + f" '{question}'")

        # Step 1: Retrieve (with relevance filtering)
        chunks = self.retrieve(question)
        print(S.get("log_retrieved", count=len(chunks)))

        if not chunks:
            print(S.get("log_no_chunks"))
            return {
                "query": question,
                "answer": S.get("not_found_answer"),
                "sources": [],
                "chunks_used": []
            }

        # Step 2: Generate
        answer, sources = await self.generate_answer(question, chunks)
        print(S.get("log_generated") + f" {sources}")

        return {
            "query": question,
            "answer": answer,
            "sources": sources,
            "chunks_used": [
                {
                    "candidate": c["metadata"]["candidate_name"],
                    "section": c["metadata"]["section"],
                    "source_file": c["metadata"]["source_file"],
                    "relevance_score": round(c.get("relevance_score", 1 - c["distance"]), 4)
                }
                for c in chunks
            ]
        }

    # -------------------------------------------------
    # UTILITY
    # -------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the vector store."""
        count = self.collection.count()
        return {
            "total_chunks_indexed": count,
            "total_documents_indexed": len(self._indexed_files),
            "embedding_model": config.EMBEDDING_MODEL,
            "embedding_dimension": self.embedding_dim,
            "indexed_files": sorted(list(self._indexed_files))
        }
