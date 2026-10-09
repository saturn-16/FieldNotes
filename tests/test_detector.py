"""Unit tests for BirdNET detector wrapper."""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from fieldnotes.detector import detect
from fieldnotes.models import Detection


def test_detect_file_not_found():
    with pytest.raises(FileNotFoundError):
        detect("non_existent_file.wav")


def test_detect_merges_duplicate_species(tmp_path):
    dummy_wav = tmp_path / "dummy.wav"
    dummy_wav.write_bytes(b"RIFF....WAVEfmt ....data....")

    # Mock dataframe with multiple segments of the same species
    mock_df = pd.DataFrame(
        [
            {
                "species_name": "Turdus migratorius_American Robin",
                "confidence": 0.65,
                "start_time": 3.0,
                "end_time": 6.0,
            },
            {
                "species_name": "Turdus migratorius_American Robin",
                "confidence": 0.88,
                "start_time": 6.0,
                "end_time": 9.0,
            },
            {
                "species_name": "Poecile atricapillus_Black-capped Chickadee",
                "confidence": 0.72,
                "start_time": 0.0,
                "end_time": 3.0,
            },
        ]
    )

    mock_result = MagicMock()
    mock_result.to_dataframe.return_value = mock_df

    mock_model = MagicMock()
    mock_model.predict.return_value = mock_result

    with patch("fieldnotes.detector._get_acoustic_model", return_value=mock_model):
        results = detect(str(dummy_wav), min_confidence=0.5)

    assert len(results) == 2
    # Verify American Robin merged with highest confidence 0.88 and first start_time 3.0
    robin = next(r for r in results if r.common_name == "American Robin")
    assert robin.scientific_name == "Turdus migratorius"
    assert robin.confidence == 0.88
    assert robin.start_s == 3.0

    chickadee = next(r for r in results if r.common_name == "Black-capped Chickadee")
    assert chickadee.confidence == 0.72
    assert chickadee.start_s == 0.0


def test_detect_empty_result(tmp_path):
    dummy_wav = tmp_path / "empty.wav"
    dummy_wav.write_bytes(b"RIFF....WAVEfmt ....data....")

    mock_result = MagicMock()
    mock_result.to_dataframe.return_value = pd.DataFrame()

    mock_model = MagicMock()
    mock_model.predict.return_value = mock_result

    with patch("fieldnotes.detector._get_acoustic_model", return_value=mock_model):
        results = detect(str(dummy_wav))

    assert results == []
