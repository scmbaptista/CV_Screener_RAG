"""
Strings Loader Module
Centralized string management for all modules.
Loads strings from data/strings.json for easy customization and localization.
"""

import json
from pathlib import Path
from typing import Dict, Any

_STRINGS_FILE = Path(__file__).parent.parent / "data" / "strings.json"
_strings_cache: Dict[str, Any] = {}


def load_strings() -> Dict[str, Any]:
    """Load all strings from the JSON file."""
    global _strings_cache
    if _strings_cache:
        return _strings_cache

    if not _STRINGS_FILE.exists():
        raise FileNotFoundError(
            f"Strings file not found: {_STRINGS_FILE}\n"
            f"Please ensure data/strings.json exists."
        )

    with open(_STRINGS_FILE, "r", encoding="utf-8") as f:
        _strings_cache = json.load(f)

    return _strings_cache


def get(module: str, key: str, **kwargs) -> str:
    """
    Get a string by module and key.

    Args:
        module: Module name (e.g., 'rag_engine', 'main', 'pdf_processor')
        key: String key within the module
        **kwargs: Format arguments for the string

    Returns:
        The formatted string
    """
    strings = load_strings()

    if module not in strings:
        return f"[MISSING_MODULE:{module}]"

    if key not in strings[module]:
        return f"[MISSING_KEY:{module}.{key}]"

    text = strings[module][key]

    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # Return unformatted if keys don't match

    return text


# Convenience accessors for each module
class RAGStrings:
    @staticmethod
    def get(key: str, **kwargs) -> str:
        return get("rag_engine", key, **kwargs)

class MainStrings:
    @staticmethod
    def get(key: str, **kwargs) -> str:
        return get("main", key, **kwargs)

class PDFStrings:
    @staticmethod
    def get(key: str, **kwargs) -> str:
        return get("pdf_processor", key, **kwargs)
