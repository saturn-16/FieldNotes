"""Generate robustness variants for clean benchmark audio clips.

For each clean clip in samples/manifest.csv:
1. noisy: adds white Gaussian noise at ~10 dB SNR
2. quiet: reduces amplitude by -12 dB (factor of ~0.251)
3. short (clipped): extracts a 5.0-second slice
"""

import csv
from pathlib import Path
import numpy as np
import soundfile as sf

SAMPLES_DIR = Path("samples")
MANIFEST_PATH = SAMPLES_DIR / "manifest.csv"


def add_gaussian_noise(audio: np.ndarray, snr_db: float = 10.0) -> np.ndarray:
    """Add zero-mean Gaussian noise to achieve target SNR in dB."""
    signal_power = np.mean(audio ** 2)
    if signal_power <= 1e-12:
        return audio.copy()
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = np.random.normal(0, np.sqrt(noise_power), size=audio.shape)
    noisy = audio + noise
    return np.clip(noisy, -1.0, 1.0).astype(np.float32)


def make_quiet(audio: np.ndarray, db_reduction: float = 12.0) -> np.ndarray:
    """Scale audio by -db_reduction dB."""
    scale = 10.0 ** (-db_reduction / 20.0)
    return (audio * scale).astype(np.float32)


def slice_clip(audio: np.ndarray, sr: int, duration_sec: float = 5.0) -> np.ndarray:
    """Extract a 5-second slice from the audio."""
    target_samples = int(duration_sec * sr)
    if len(audio) <= target_samples:
        return audio.copy()
    # Take a slice starting at 2.0s if possible, or middle
    start = min(int(2.0 * sr), len(audio) - target_samples)
    return audio[start : start + target_samples].copy()


def generate_variants():
    if not MANIFEST_PATH.exists():
        print(f"Manifest {MANIFEST_PATH} not found.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    fieldnames = ["file", "expected_common_name", "expected_scientific_name",
                  "source_url", "license", "attribution", "condition"]
    
    clean_rows = [r for r in reader if r.get("condition") == "clean"]
    new_rows = list(reader)

    print(f"Found {len(clean_rows)} clean clips to generate variants from.")
    np.random.seed(42)  # reproducible noise

    for row in clean_rows:
        clip_path = SAMPLES_DIR / row["file"]
        if not clip_path.exists():
            print(f"File {clip_path} does not exist, skipping variants.")
            continue

        audio, sr = sf.read(str(clip_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        base_stem = clip_path.stem

        # 1. Noisy (~10 dB SNR)
        noisy_name = f"{base_stem}_noisy.wav"
        noisy_path = SAMPLES_DIR / noisy_name
        noisy_audio = add_gaussian_noise(audio, snr_db=10.0)
        sf.write(str(noisy_path), noisy_audio, sr)
        new_rows.append({
            "file": noisy_name,
            "expected_common_name": row["expected_common_name"],
            "expected_scientific_name": row["expected_scientific_name"],
            "source_url": row["source_url"],
            "license": row["license"],
            "attribution": row["attribution"],
            "condition": "noisy",
        })

        # 2. Quiet (-12 dB)
        quiet_name = f"{base_stem}_quiet.wav"
        quiet_path = SAMPLES_DIR / quiet_name
        quiet_audio = make_quiet(audio, db_reduction=12.0)
        sf.write(str(quiet_path), quiet_audio, sr)
        new_rows.append({
            "file": quiet_name,
            "expected_common_name": row["expected_common_name"],
            "expected_scientific_name": row["expected_scientific_name"],
            "source_url": row["source_url"],
            "license": row["license"],
            "attribution": row["attribution"],
            "condition": "quiet",
        })

        # 3. Short (5s slice)
        short_name = f"{base_stem}_short.wav"
        short_path = SAMPLES_DIR / short_name
        short_audio = slice_clip(audio, sr, duration_sec=5.0)
        sf.write(str(short_path), short_audio, sr)
        new_rows.append({
            "file": short_name,
            "expected_common_name": row["expected_common_name"],
            "expected_scientific_name": row["expected_scientific_name"],
            "source_url": row["source_url"],
            "license": row["license"],
            "attribution": row["attribution"],
            "condition": "short",
        })

        print(f"Generated noisy, quiet, short variants for {row['file']}.")

    # Deduplicate rows by file
    seen = set()
    deduped = []
    for r in new_rows:
        if r["file"] not in seen:
            seen.add(r["file"])
            deduped.append(r)

    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    print(f"Updated manifest at {MANIFEST_PATH} with {len(deduped)} total rows.")


if __name__ == "__main__":
    generate_variants()
