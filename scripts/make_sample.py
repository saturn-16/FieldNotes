"""Sample audio generator for Field Notes.

Generates test WAV clips containing synthetic bird calls and chirps
for offline verification without relying on external network downloads.
"""

import math
import struct
import wave
from pathlib import Path


def create_bird_chirp(
    output_path: Path | str,
    duration_s: float = 4.0,
    sample_rate: int = 48000,
    base_freq: float = 3500.0,
    chirp_rate: float = 4.0,
) -> Path:
    """Generate a clean synthetic bird chirp clip."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    n_samples = int(duration_s * sample_rate)
    frames = bytearray()

    for i in range(n_samples):
        t = i / sample_rate
        # Pulsing frequency sweep simulating a warbler or sparrow call
        freq = base_freq + 1200.0 * math.sin(2.0 * math.pi * chirp_rate * t)
        envelope = 0.5 * (1.0 + math.cos(2.0 * math.pi * chirp_rate * t))
        amplitude = 32767.0 * 0.45 * (envelope ** 2)
        sample = int(amplitude * math.sin(2.0 * math.pi * freq * t))
        sample = max(-32768, min(32767, sample))
        frames.extend(struct.pack("<h", sample))

    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)

    return out_file


def generate_all_samples():
    """Generate multiple sample clips in the samples/ folder."""
    samples_dir = Path("samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    c1 = create_bird_chirp(samples_dir / "synthetic_chirp.wav", duration_s=4.0, base_freq=3200.0, chirp_rate=3.5)
    c2 = create_bird_chirp(samples_dir / "high_pitch_warble.wav", duration_s=3.5, base_freq=4800.0, chirp_rate=5.0)
    c3 = create_bird_chirp(samples_dir / "rapid_trill.wav", duration_s=3.0, base_freq=2800.0, chirp_rate=8.0)

    print(f"Generated sample clips in {samples_dir.resolve()}:")
    print(f"- {c1.name}")
    print(f"- {c2.name}")
    print(f"- {c3.name}")


if __name__ == "__main__":
    generate_all_samples()
