"""Full end-to-end integration flow test."""

from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd

from fieldnotes.detector import detect
from fieldnotes.journal import generate_entry
from fieldnotes.lifelist import add_sightings, get_life_list, weekly_progress


def test_full_pipeline_flow(tmp_path):
    # 1. Prepare simulated audio clip and database
    test_wav = tmp_path / "test_recording.wav"
    test_wav.write_bytes(b"RIFF....WAVEfmt ....data....")
    test_db = tmp_path / "fieldnotes_test.db"

    # 2. Mock BirdNET output with 2 detected bird species
    mock_df = pd.DataFrame(
        [
            {
                "species_name": "Turdus migratorius_American Robin",
                "confidence": 0.89,
                "start_time": 0.0,
                "end_time": 3.0,
            },
            {
                "species_name": "Cardinalis cardinalis_Northern Cardinal",
                "confidence": 0.94,
                "start_time": 3.0,
                "end_time": 6.0,
            },
        ]
    )
    mock_res = MagicMock()
    mock_res.to_dataframe.return_value = mock_df

    mock_model = MagicMock()
    mock_model.predict.return_value = mock_res

    with patch("fieldnotes.detector._get_acoustic_model", return_value=mock_model):
        detections = detect(str(test_wav), min_confidence=0.5)

    assert len(detections) == 2
    assert detections[0].common_name == "Northern Cardinal"  # highest confidence first
    assert detections[1].common_name == "American Robin"

    # 3. Add to Life List & Check Weekly Goal
    now = datetime.now()
    new_species = add_sightings(detections, "Oak Grove", now, db_path=test_db)
    assert set(new_species) == {"American Robin", "Northern Cardinal"}

    life_list = get_life_list(db_path=test_db)
    assert len(life_list) == 2

    count_week, goal = weekly_progress(goal=5, db_path=test_db)
    assert count_week == 2
    assert goal == 5

    # 4. Generate Journal Entry
    mock_llm_text = (
        "Spent a peaceful morning at Oak Grove. The woods were lively with the clear, "
        "whistled cheer of a Northern Cardinal and the cheerful caroling of an American Robin. "
        "Fun fact: Northern Cardinals mate for life and often sing duets together. "
        "Fun fact: American Robins have excellent eyesight and can locate earthworms visually. "
        "Listen for next time: Notice the robin's rising-and-falling 'cheerily, cheer-up' rhythm."
    )
    with patch("ollama.chat", return_value={"message": {"content": mock_llm_text}}):
        entry = generate_entry(detections, "Oak Grove", now, model="llama3.2:3b")

    assert "Northern Cardinal" in entry
    assert "American Robin" in entry
    assert "Listen for next time" in entry
