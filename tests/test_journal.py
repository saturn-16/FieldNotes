"""Unit and integration tests for field journal generation."""

from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
import ollama

from fieldnotes.journal import generate_entry
from fieldnotes.models import Detection
from fieldnotes.config import DEFAULT_MODEL, get_available_ollama_models


def test_empty_detections_no_llm_call():
    """Verify that empty detections gracefully return without calling Ollama."""
    with patch("ollama.chat") as mock_chat:
        entry = generate_entry(
            detections=[],
            place="Oak Park",
            when=datetime(2026, 10, 9, 7, 30),
            model="llama3.2:3b",
        )
        mock_chat.assert_not_called()
        assert "No clear calls this time" in entry
        assert "Oak Park" in entry


def test_generate_entry_calls_ollama_with_temperature():
    """Verify that detections are passed with low temperature to Ollama."""
    detections = [
        Detection(
            common_name="American Robin",
            scientific_name="Turdus migratorius",
            confidence=0.91,
            start_s=1.0,
            end_s=4.0,
        ),
        Detection(
            common_name="Blue Jay",
            scientific_name="Cyanocitta cristata",
            confidence=0.85,
            start_s=5.0,
            end_s=8.0,
        ),
    ]

    mock_response = {
        "message": {
            "content": "A crisp morning with robins and jays active in the trees."
        }
    }

    with patch("ollama.chat", return_value=mock_response) as mock_chat:
        entry = generate_entry(
            detections=detections,
            place="Pine Hollow",
            when=datetime(2026, 10, 9, 8, 0),
            model="llama3.2:3b",
        )

        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["model"] == "llama3.2:3b"
        assert call_kwargs["options"]["temperature"] == 0.4

        prompt = call_kwargs["messages"][0]["content"]
        assert "American Robin" in prompt
        assert "Turdus migratorius" in prompt
        assert "Blue Jay" in prompt
        assert "Pine Hollow" in prompt
        assert "Rely ONLY on the detected species" in prompt
        assert entry == "A crisp morning with robins and jays active in the trees."


def test_ollama_connection_error_handling():
    """Verify clear error message when Ollama is unreachable."""
    detections = [
        Detection("House Sparrow", "Passer domesticus", 0.8, 0.0, 3.0)
    ]
    with patch("ollama.chat", side_effect=Exception("Connection refused")):
        entry = generate_entry(detections, "Garden", datetime.now(), "llama3.2:3b")
        assert "Error: Unable to connect to Ollama service" in entry


def test_ollama_model_missing_error_handling():
    """Verify clear error message when model is missing."""
    detections = [
        Detection("House Sparrow", "Passer domesticus", 0.8, 0.0, 3.0)
    ]
    error = ollama.ResponseError("model not found", status_code=404)
    with patch("ollama.chat", side_effect=error):
        entry = generate_entry(detections, "Garden", datetime.now(), "non_existent_model")
        assert "Model 'non_existent_model' may not be available" in entry


def test_live_entry_generation_if_model_available():
    """Optional live test running against locally available Ollama model."""
    models = get_available_ollama_models()
    if not models:
        pytest.skip("No local Ollama models found.")

    test_model = models[0]
    detections = [
        Detection(
            common_name="American Robin",
            scientific_name="Turdus migratorius",
            confidence=0.88,
            start_s=0.0,
            end_s=3.0,
        )
    ]
    entry = generate_entry(
        detections=detections,
        place="Forest Trail",
        when=datetime.now(),
        model=test_model,
    )
    assert len(entry) > 30
    assert "Robin" in entry or "Turdus" in entry
