"""BirdNET detection wrapper for Field Notes."""

import sys
from pathlib import Path
from typing import Any
import pandas as pd

from fieldnotes.models import Detection

_acoustic_model: Any = None


def _get_acoustic_model() -> Any:
    """Lazily load and cache the BirdNET acoustic model."""
    global _acoustic_model
    if _acoustic_model is None:
        import birdnet

        _acoustic_model = birdnet.load("acoustic", "2.4", "tf", library="litert")
    return _acoustic_model


def detect(
    audio_path: str,
    lat: float | None = None,
    lon: float | None = None,
    week: int | None = None,
    min_confidence: float = 0.5,
) -> list[Detection]:
    """Detect bird species in an audio file using BirdNET.

    Merges duplicate species across time windows, keeping the highest confidence
    and the earliest start time.
    """
    path_obj = Path(audio_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _get_acoustic_model()

    custom_species_list: list[str] | None = None
    if lat is not None and lon is not None:
        try:
            import birdnet

            geo_model = birdnet.load("geo", "2.4", "tf", library="litert")
            geo_res = geo_model.predict(lat, lon, week=week)
            custom_species_list = list(geo_res.to_set())
        except Exception:
            custom_species_list = None

    predict_kwargs: dict[str, Any] = {
        "default_confidence_threshold": min_confidence,
    }
    if custom_species_list:
        predict_kwargs["custom_species_list"] = custom_species_list

    result = model.predict(str(path_obj.resolve()), **predict_kwargs)
    df = result.to_dataframe()

    if df.empty:
        return []

    # Parse detections
    raw_detections: list[Detection] = []
    for _, row in df.iterrows():
        species_raw = str(row.get("species_name", ""))
        confidence = float(row.get("confidence", 0.0))
        start_s = float(row.get("start_time", 0.0))
        end_s = float(row.get("end_time", 0.0))

        if confidence < min_confidence:
            continue

        if "_" in species_raw:
            parts = species_raw.split("_", 1)
            scientific_name = parts[0].strip()
            common_name = parts[1].strip()
        else:
            scientific_name = species_raw.strip()
            common_name = species_raw.strip()

        raw_detections.append(
            Detection(
                common_name=common_name,
                scientific_name=scientific_name,
                confidence=confidence,
                start_s=start_s,
                end_s=end_s,
            )
        )

    # Merge duplicates across time windows
    merged: dict[str, Detection] = {}
    for det in raw_detections:
        key = det.common_name
        if key not in merged:
            merged[key] = Detection(
                common_name=det.common_name,
                scientific_name=det.scientific_name,
                confidence=det.confidence,
                start_s=det.start_s,
                end_s=det.end_s,
            )
        else:
            current = merged[key]
            if det.confidence > current.confidence:
                current.confidence = det.confidence
            if det.start_s < current.start_s:
                current.start_s = det.start_s
                current.end_s = det.end_s

    # Sort descending by confidence
    return sorted(merged.values(), key=lambda d: d.confidence, reverse=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m fieldnotes.detector <audio_file.wav>")
        sys.exit(1)

    file_arg = sys.argv[1]
    detections = detect(file_arg)
    if not detections:
        print("No bird calls detected above confidence threshold.")
    else:
        print(f"Detected {len(detections)} species:")
        for d in detections:
            print(
                f"- {d.common_name} ({d.scientific_name}): "
                f"confidence={d.confidence:.2f}, window=[{d.start_s:.1f}s - {d.end_s:.1f}s]"
            )
