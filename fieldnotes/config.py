"""Configuration settings and model detection for Field Notes."""

from pathlib import Path
import ollama

DEFAULT_MODEL: str = "llama3.2:3b"
DEFAULT_CONFIDENCE: float = 0.5
DB_PATH: Path = Path("fieldnotes.db")


def get_available_ollama_models() -> list[str]:
    """Return a list of locally available Ollama model tags."""
    try:
        response = ollama.list()
        models: list[str] = []
        model_list = getattr(response, "models", []) or response.get("models", [])
        for item in model_list:
            if hasattr(item, "model"):
                models.append(item.model)
            elif isinstance(item, dict) and "model" in item:
                models.append(item["model"])
            elif isinstance(item, dict) and "name" in item:
                models.append(item["name"])
        return models
    except Exception:
        return []
