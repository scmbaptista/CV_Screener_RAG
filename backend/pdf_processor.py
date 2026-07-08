"""
PDF Processor Module
Extracts structured text from CV PDFs with section-aware parsing.
Uses pdfplumber for high-quality text extraction and preserves
section boundaries for better chunking.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
from dictionary import PDFStrings as S


class CVDocument:
    """Represents a parsed CV document with metadata and sections."""

    def __init__(self, filepath: Path, raw_text: str, sections: Dict[str, str], metadata: Dict[str, Any]):
        self.filepath = filepath
        self.filename = filepath.name
        self.raw_text = raw_text
        self.sections = sections
        self.metadata = metadata
        self.candidate_name = self._extract_name()

    def _extract_name(self) -> str:
        """Try to extract candidate name from filename or first line."""
        # From filename: cv_001_john_doe.pdf -> John Doe
        match = re.search(r'cv_\d+_(.+?)\.pdf$', self.filename)
        if match:
            return match.group(1).replace('_', ' ').title()
        # Fallback: first line of text
        first_line = self.raw_text.strip().split('\n')[0]
        return first_line.strip()[:50]


def extract_text_from_pdf(filepath: Path) -> str:
    """Extract full text from a PDF file using pdfplumber."""
    text_parts = []
    with pdfplumber.open(str(filepath)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def detect_sections(text: str) -> Dict[str, str]:
    """
    Detect common CV sections using regex patterns.
    Returns a dict of section_name -> section_content.
    """
    # Common section headers (case-insensitive)
    section_patterns = [
        S.get("section_summary"),
        S.get("section_experience"),
        S.get("section_education"),
        S.get("section_skills"),
        S.get("section_languages"),
        S.get("section_certifications"),
        S.get("section_projects"),
        S.get("section_awards")
    ]

    sections = {}

    # Split text by potential section headers
    # We build a combined regex that captures any section header
    combined_pattern = '|'.join(f'({p})' for p in section_patterns)

    # Find all section boundaries
    matches = list(re.finditer(combined_pattern, text, re.IGNORECASE))

    if not matches:
        # No sections found, return whole text as "content"
        return {"content": text.strip()}

    for i, match in enumerate(matches):
        section_name = match.group(0).strip().upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start:end].strip()

        # Clean up: remove footer artifacts
        section_content = re.sub(S.get("footer_filter"), '', section_content)
        section_content = section_content.strip()

        if section_content:
            sections[section_name] = section_content

    return sections


def parse_cv(filepath: Path) -> CVDocument:
    """
    Parse a single CV PDF into a structured document.
    """
    raw_text = extract_text_from_pdf(filepath)
    sections = detect_sections(raw_text)

    # Extract metadata heuristics
    metadata = {
        "source_file": filepath.name,
        "word_count": len(raw_text.split()),
        "section_count": len(sections),
        "section_names": list(sections.keys())
    }

    return CVDocument(filepath, raw_text, sections, metadata)


def process_all_cvs(cv_dir: Path) -> List[CVDocument]:
    """
    Process all CV PDFs in a directory.
    Returns a list of CVDocument objects.
    """
    cv_files = sorted(cv_dir.glob("cv_*.pdf"))
    documents = []

    print(S.get("log_processing", count=len(cv_files), dir=cv_dir))
    for cv_file in cv_files:
        try:
            doc = parse_cv(cv_file)
            documents.append(doc)
            print(S.get("log_parsed", name=doc.candidate_name, filename=doc.filename))
        except Exception as e:
            print(S.get("log_failed", filename=cv_file.name, error=e))

    print(S.get("log_success", count=len(documents)))
    return documents
