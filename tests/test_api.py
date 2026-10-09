"""API tests for FastAPI endpoints in main.py."""

import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from fieldnotes.models import Detection
from main import app, init_journal_db


@pytest.fixture
def client(tmp_path):
    test_db = tmp_path / "test_api.db"
    init_journal_db(test_db)
    with patch("main.DB_PATH", test_db), patch("fieldnotes.lifelist.DB_PATH", test_db):
        with TestClient(app) as test_client:
            yield test_client


def test_get_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Field Notes" in response.text
    assert "<!DOCTYPE html>" in response.text


def test_get_models(client):
    with patch("main.get_available_ollama_models", return_value=["llama3.2:3b"]):
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "llama3.2:3b" in data["models"]


def test_empty_audio_upload_error(client):
    files = {"audio": ("test.wav", b"", "audio/wav")}
    response = client.post("/api/identify", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_model_missing_error(client):
    fake_wav = b"RIFF....WAVEfmt ....data...."
    files = {"audio": ("test.wav", fake_wav, "audio/wav")}
    data = {"model": "non_existent_model"}

    with patch("main.get_available_ollama_models", return_value=["llama3.2:3b"]):
        response = client.post("/api/identify", files=files, data=data)
        assert response.status_code == 400
        assert "not pulled locally" in response.json()["detail"]


def test_ollama_not_running_error(client):
    fake_wav = b"RIFF....WAVEfmt ....data...."
    files = {"audio": ("test.wav", fake_wav, "audio/wav")}
    data = {"model": "llama3.2:3b"}

    with patch("main.get_available_ollama_models", return_value=["llama3.2:3b"]), \
         patch("main.detect", return_value=[]), \
         patch("main.generate_entry", return_value="Error: Unable to connect to Ollama service"):
        response = client.post("/api/identify", files=files, data=data)
        assert response.status_code == 503
        assert "Ollama isn't running" in response.json()["detail"]


def test_successful_identification_and_export(client):
    fake_wav = b"RIFF....WAVEfmt ....data...."
    files = {"audio": ("sample.wav", fake_wav, "audio/wav")}
    form_data = {
        "place": "Silver Falls",
        "min_confidence": "0.6",
        "model": "llama3.2:3b",
    }

    mock_detections = [
        Detection(
            common_name="Steller's Jay",
            scientific_name="Cyanocitta stelleri",
            confidence=0.92,
            start_s=1.2,
            end_s=4.2,
        )
    ]
    mock_journal = "A magnificent Steller's Jay called from the high hemlocks."

    with patch("main.get_available_ollama_models", return_value=["llama3.2:3b"]), \
         patch("main.detect", return_value=mock_detections), \
         patch("main.generate_entry", return_value=mock_journal):
        response = client.post("/api/identify", files=files, data=form_data)
        assert response.status_code == 200
        result = response.json()
        assert len(result["detections"]) == 1
        assert result["detections"][0]["common_name"] == "Steller's Jay"
        assert result["new_species"] == ["Steller's Jay"]
        assert result["journal"] == mock_journal
        entry_id = result["entry_id"]

    # Verify export endpoint
    export_resp = client.get(f"/api/export/{entry_id}")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/markdown")
    assert "Steller's Jay" in export_resp.text


def test_export_not_found(client):
    response = client.get("/api/export/999999")
    assert response.status_code == 404


def test_lifelist_and_weekly_endpoints(client):
    life_resp = client.get("/api/lifelist")
    assert life_resp.status_code == 200
    assert isinstance(life_resp.json(), list)

    weekly_resp = client.get("/api/weekly?goal=5")
    assert weekly_resp.status_code == 200
    data = weekly_resp.json()
    assert "count" in data
    assert data["goal"] == 5
