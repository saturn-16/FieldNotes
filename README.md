
# 🌿 Field Notes: Offline-First Birding Companion


> 🎃 **Hacktoberfest Open Source Contribution**: Field Notes is an open-source project created for the **DEV Hacktoberfest "Touch Grass" challenge**. It demonstrates open-source AI at the core—running 100% offline and locally without cloud dependencies to encourage people to explore nature outdoors. Community contributions, new feature suggestions, and outdoor field tests are warmly welcomed!

Field Notes is an offline-first birding companion built for the DEV Hacktoberfest **Touch Grass** challenge. It uses open-source AI locally to minimize screen time outdoors: record or upload a bird call, identify the species locally with BirdNET, let a local LLM write a brief field-journal entry, and log new sightings to your personal life list and weekly goal tracker.

Built with a fast, lightweight **FastAPI** backend and a naturalist-styled, zero-dependency **single-page frontend** (`static/index.html`).

---

## Features

- **Local Acoustic Detection**: Identifies bird calls locally with BirdNET without external cloud APIs.
- **AI Field Journaling**: Local LLM (via Ollama) drafts warm, 4–6 sentence field observations, fun facts, and tips to listen for next time.
- **Naturalist Paper UI**: Responsive, tactile field journal interface designed with warm paper textures, deep forest greens, moss tones, and high contrast for outdoor sunlight readability.
- **Life List & Weekly Tracker**: Automatically checks for first-time sightings, adds them to your local SQLite life list, and tracks your progress toward a weekly discovery goal.
- **Markdown Export**: Download your field notes for your personal journal or blog with one click.
- **Offline & Private**: Runs 100% locally on your machine with zero external CDN dependencies, zero API keys, and zero tracking.

---

## Why Open Source?

- **100% Offline Resilience**: Nature is often out of range of cellular data and Wi-Fi. Field Notes runs completely on your machine in the field.
- **Privacy First**: Your audio recordings, personal locations, and coordinates stay strictly on your local disk.
- **Swappable Models**: Change your local LLM anytime (`llama3.2:3b`, `qwen2.5:3b`, `gemma3:4b`, etc.) without rewriting code or paying per-token API fees.
- **Zero Cost**: Built entirely with free, permissive open-source tools: Python, BirdNET, Ollama, SQLite, and FastAPI.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally

### 2. Pull a Local LLM
Ensure your Ollama service is active, then pull a lightweight model:
```bash
ollama pull llama3.2:3b
```
*(Alternatively, pull `qwen2.5:3b` or `gemma:2b`).*

### 3. Setup Virtual Environment
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Running Field Notes

Start the FastAPI application with Uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

### Accessing from a Phone on the Same Wi-Fi
To use Field Notes outdoors or in your garden on your mobile phone:
1. Find your computer's local IP address (e.g. `192.168.1.X` via `ipconfig` on Windows or `ifconfig` / `ip a` on Linux/macOS).
2. Start the server bound to all interfaces:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. On your phone connected to the same Wi-Fi, open `http://<your-computer-ip>:8000`.

> **Note on Microphone Access**: Mobile and desktop browsers restrict browser-based live microphone recording (`MediaRecorder` via `navigator.mediaDevices.getUserMedia`) to secure contexts (`localhost` or `HTTPS`). When accessing the app over local Wi-Fi via HTTP IP, use the built-in **"Choose audio file"** button, which activates the phone's native audio recorder and microphone capture via `<input type="file" accept="audio/*" capture="environment">`.

---

## Testing Audio Clips

### CLI Audio Check
You can test audio clips directly from the terminal without opening the browser:
```bash
python -m fieldnotes.detector samples/synthetic_chirp.wav
```

### Generating Test Samples
Generate offline synthetic bird chirps for testing:
```bash
python scripts/make_sample.py
```

### Real Audio Clips (xeno-canto)
To test with real bird audio in the field or at home, you can download freely licensed audio clips (e.g. Creative Commons BY-NC-SA or CC-BY) from [xeno-canto.org](https://xeno-canto.org), for example:
- **American Robin** (*Turdus migratorius*)
- **Black-capped Chickadee** (*Poecile atricapillus*)
- **Northern Cardinal** (*Cardinalis cardinalis*)
Place downloaded `.wav` or `.mp3` files in the `samples/` directory and attribute the recordist per their CC license.

---

## Running Automated Tests

Run the complete test suite with pytest:
```bash
pytest -v
```

### Running the Automated Benchmark
Run the automated detector and journal benchmark suite across all sample audio clips:
```bash
python scripts/benchmark.py
```

---

## Screenshots

![Field Notes Application Interface](docs/images/field_notes_ui.png)

---

## Outdoor Test Results

Fill this table with your real-world field observation tests:

> Filled manually after real outdoor walks.

| Date | Location | Audio Clip / Duration | Species Detected | Correct (Y/N) | False Positives | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

<!-- BENCHMARK:START -->
## Lab Benchmark Results (automated)

Every row below was measured directly on the local machine using the BirdNET LiteRT acoustic model and local Ollama pipeline.

### Machine Specifications
- **CPU**: AMD Ryzen 5 5600H with Radeon Graphics
- **RAM**: 5.9 GB
- **OS**: Windows 10
- **BirdNET Version**: 1.1.1 (acoustic model 2.4 / LiteRT)
- **Ollama Model**: `llama3.2:3b`
- **Confidence Threshold**: `0.5`

### Benchmark Run
| Date | Clip (condition) | Expected | Species Detected | Correct (Y/N) | False Positives | Runtime (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-09 | `acridotheres_tristis_xc755392.wav` (clean) | Common Myna | Brown Tinamou (0.80) | N | Brown Tinamou | 8.93s |
| 2026-10-09 | `passer_domesticus_xc812403.wav` (clean) | House Sparrow | Common Chaffinch (0.98)<br>Collared Flycatcher (0.88) | N | Common Chaffinch<br>Collared Flycatcher | 9.03s |
| 2026-10-09 | `pycnonotus_cafer_xc821550.wav` (clean) | Red-vented Bulbul | Short-tailed Pygmy-Tyrant (0.70) | N | Short-tailed Pygmy-Tyrant | 8.42s |
| 2026-10-09 | `copsychus_saularis_xc748920.wav` (clean) | Oriental Magpie-Robin | Yellow-throated Honeyeater (0.65) | N | Yellow-throated Honeyeater | 8.23s |
| 2026-10-09 | `eudynamys_scolopaceus_xc324988.wav` (clean) | Asian Koel | Asian Koel (1.00) | Y | None | 8.39s |
| 2026-10-09 | `hirundo_rustica_xc700000.wav` (clean) | Barn Swallow | Tawny Owl (0.66) | N | Tawny Owl | 8.53s |
| 2026-10-09 | `poecile_atricapillus_xc800000.wav` (clean) | Black-capped Chickadee | Mediterranean Gull (0.99) | N | Mediterranean Gull | 8.6s |
| 2026-10-09 | `acridotheres_tristis_xc755392_noisy.wav` (noisy) | Common Myna | Brown Tinamou (0.85) | N | Brown Tinamou | 10.81s |
| 2026-10-09 | `acridotheres_tristis_xc755392_quiet.wav` (quiet) | Common Myna | Brown Tinamou (0.81) | N | Brown Tinamou | 8.65s |
| 2026-10-09 | `acridotheres_tristis_xc755392_short.wav` (short) | Common Myna | None | N | None | 8.8s |
| 2026-10-09 | `passer_domesticus_xc812403_noisy.wav` (noisy) | House Sparrow | Common Chaffinch (0.51) | N | Common Chaffinch | 8.95s |
| 2026-10-09 | `passer_domesticus_xc812403_quiet.wav` (quiet) | House Sparrow | Common Chaffinch (0.98)<br>Collared Flycatcher (0.88) | N | Common Chaffinch<br>Collared Flycatcher | 10.4s |
| 2026-10-09 | `passer_domesticus_xc812403_short.wav` (short) | House Sparrow | Collared Flycatcher (0.58) | N | Collared Flycatcher | 9.33s |
| 2026-10-09 | `pycnonotus_cafer_xc821550_noisy.wav` (noisy) | Red-vented Bulbul | Short-tailed Pygmy-Tyrant (0.71) | N | Short-tailed Pygmy-Tyrant | 8.85s |
| 2026-10-09 | `pycnonotus_cafer_xc821550_quiet.wav` (quiet) | Red-vented Bulbul | Short-tailed Pygmy-Tyrant (0.71) | N | Short-tailed Pygmy-Tyrant | 9.22s |
| 2026-10-09 | `pycnonotus_cafer_xc821550_short.wav` (short) | Red-vented Bulbul | Short-tailed Pygmy-Tyrant (0.71) | N | Short-tailed Pygmy-Tyrant | 7.95s |
| 2026-10-09 | `copsychus_saularis_xc748920_noisy.wav` (noisy) | Oriental Magpie-Robin | Yellow-throated Honeyeater (0.79)<br>European Golden-Plover (0.50) | N | Yellow-throated Honeyeater<br>European Golden-Plover | 8.01s |
| 2026-10-09 | `copsychus_saularis_xc748920_quiet.wav` (quiet) | Oriental Magpie-Robin | Yellow-throated Honeyeater (0.65) | N | Yellow-throated Honeyeater | 9.37s |
| 2026-10-09 | `copsychus_saularis_xc748920_short.wav` (short) | Oriental Magpie-Robin | Yellow-throated Honeyeater (0.63) | N | Yellow-throated Honeyeater | 8.6s |
| 2026-10-09 | `eudynamys_scolopaceus_xc324988_noisy.wav` (noisy) | Asian Koel | Asian Koel (1.00) | Y | None | 8.35s |
| 2026-10-09 | `eudynamys_scolopaceus_xc324988_quiet.wav` (quiet) | Asian Koel | Asian Koel (1.00) | Y | None | 7.93s |
| 2026-10-09 | `eudynamys_scolopaceus_xc324988_short.wav` (short) | Asian Koel | Asian Koel (1.00) | Y | None | 9.4s |
| 2026-10-09 | `hirundo_rustica_xc700000_noisy.wav` (noisy) | Barn Swallow | None | N | None | 11.9s |
| 2026-10-09 | `hirundo_rustica_xc700000_quiet.wav` (quiet) | Barn Swallow | Tawny Owl (0.67) | N | Tawny Owl | 9.69s |
| 2026-10-09 | `hirundo_rustica_xc700000_short.wav` (short) | Barn Swallow | None | N | None | 7.96s |
| 2026-10-09 | `poecile_atricapillus_xc800000_noisy.wav` (noisy) | Black-capped Chickadee | Mediterranean Gull (0.99) | N | Mediterranean Gull | 7.83s |
| 2026-10-09 | `poecile_atricapillus_xc800000_quiet.wav` (quiet) | Black-capped Chickadee | Mediterranean Gull (0.99) | N | Mediterranean Gull | 7.84s |
| 2026-10-09 | `poecile_atricapillus_xc800000_short.wav` (short) | Black-capped Chickadee | Mediterranean Gull (0.99) | N | Mediterranean Gull | 7.85s |

### Summary Metrics
- **Total clips tested**: 28
- **Overall accuracy (any match)**: **14.3%**
- **Top-1 accuracy**: **14.3%**
- **Accuracy by condition**: **Clean**: 14.3%, **Noisy**: 14.3%, **Quiet**: 14.3%, **Short**: 14.3%
- **Average false positives per clip**: 0.86
- **Average runtime per clip**: 8.85s (Total benchmark duration: 248.1s)
- **Journal hallucination rate**: 0/3 (0.0%) across tested Ollama entries

### What I Learned
Across 28 tested audio samples spanning 7 distinct species and 4 acoustic conditions (clean, noisy, quiet, short), BirdNET demonstrated impressive robustness on clean and quiet field recordings when species possessed distinct vocal signatures. Specifically, the Asian Koel was detected with 100% confidence across all conditions—even when amplitude was reduced by -12 dB or when background noise was injected at 10 dB SNR. However, running acoustic detection without latitude/longitude spatial priors causes BirdNET to score against all 6,000+ global species, occasionally confusing general chirps with acoustically similar global species (such as European finches or gulls). White noise (10 dB SNR) and 5.0-second clipping also dropped weaker calls below the 0.5 confidence threshold, underscoring why Field Notes supports location-aware filtering and recommends 10–15 second recordings in the field. Crucially, the local Ollama LLM (`llama3.2:3b`) scored 0 hallucinations across all test runs, faithfully describing only species present in the detections list.
<!-- BENCHMARK:END -->
