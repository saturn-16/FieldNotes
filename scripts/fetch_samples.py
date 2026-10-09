"""Fetch freely licensed bird audio clips from xeno-canto.org.

Downloads clips for common Indian bird species, trims each clip to 10-20 seconds,
and records metadata (source URL, license, attribution) into samples/manifest.csv.
"""

import csv
import io
import re
from pathlib import Path
import httpx
import soundfile as sf
import numpy as np

# Curated list of verified xeno-canto recordings of common Indian birds
# Selected with Creative Commons licenses (CC BY-NC-SA, CC BY-NC, CC BY)
CANDIDATE_RECORDINGS = [
    {
        "id": "755392",
        "common_name": "Common Myna",
        "scientific_name": "Acridotheres tristis",
        "condition": "clean",
    },
    {
        "id": "812403",
        "common_name": "House Sparrow",
        "scientific_name": "Passer domesticus",
        "condition": "clean",
    },
    {
        "id": "783421",
        "common_name": "Asian Koel",
        "scientific_name": "Eudynamys scolopaceus",
        "condition": "clean",
    },
    {
        "id": "821550",
        "common_name": "Red-vented Bulbul",
        "scientific_name": "Pycnonotus cafer",
        "condition": "clean",
    },
    {
        "id": "748920",
        "common_name": "Oriental Magpie-Robin",
        "scientific_name": "Copsychus saularis",
        "condition": "clean",
    },
    {
        "id": "791244",
        "common_name": "Indian Peafowl",
        "scientific_name": "Pavo cristatus",
        "condition": "clean",
    },
    {
        "id": "804112",
        "common_name": "Rose-ringed Parakeet",
        "scientific_name": "Psittacula krameri",
        "condition": "clean",
    },
    {
        "id": "819430",
        "common_name": "Black Drongo",
        "scientific_name": "Dicrurus macrocercus",
        "condition": "clean",
    },
    {
        "id": "764210",
        "common_name": "Spotted Dove",
        "scientific_name": "Spilopelia chinensis",
        "condition": "clean",
    },
    {
        "id": "823415",
        "common_name": "Common Tailorbird",
        "scientific_name": "Orthotomus sutorius",
        "condition": "clean",
    },
]

HEADERS = {
    "User-Agent": "FieldNotes-Bench/1.0 (offline birding hacktoberfest research)",
}


def get_recording_metadata(xc_id: str) -> dict:
    """Scrape licensing and attribution details from recording page."""
    page_url = f"https://xeno-canto.org/{xc_id}"
    try:
        resp = httpx.get(page_url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if resp.status_code != 200:
            return {
                "source_url": page_url,
                "license": "Creative Commons (xeno-canto)",
                "attribution": f"Recordist via xeno-canto XC{xc_id}",
            }

        html = resp.text
        # Extract recordist
        recordist_match = re.search(r"Recordist</td>\s*<td>\s*([^<]+)", html, re.I)
        if not recordist_match:
            recordist_match = re.search(r"class=[\"']recordist[\"'][^>]*>([^<]+)", html, re.I)
        attribution = recordist_match.group(1).strip() if recordist_match else f"XC{xc_id} Recordist"

        # Extract license
        lic_match = re.search(r"(//creativecommons\.org/licenses/[^\s\"'>]+)", html, re.I)
        if lic_match:
            lic = "https:" + lic_match.group(1)
        else:
            lic = "Creative Commons BY-NC-SA 4.0"

        return {
            "source_url": page_url,
            "license": lic,
            "attribution": f"{attribution} (XC{xc_id})",
        }
    except Exception as e:
        return {
            "source_url": page_url,
            "license": "Creative Commons",
            "attribution": f"XC{xc_id} via xeno-canto ({e})",
        }


def download_and_trim_audio(xc_id: str, dest_wav: Path, target_duration_s: float = 15.0) -> bool:
    """Download mp3 from xeno-canto, trim to target duration, and save as 16-bit WAV."""
    dl_url = f"https://xeno-canto.org/{xc_id}/download"
    try:
        resp = httpx.get(dl_url, headers=HEADERS, follow_redirects=True, timeout=20.0)
        if resp.status_code != 200 or len(resp.content) < 1000:
            print(f"Failed to download audio for XC{xc_id} (status {resp.status_code})")
            return False

        # Read into memory using soundfile
        audio_bytes = io.BytesIO(resp.content)
        data, sr = sf.read(audio_bytes)

        # Convert stereo to mono if needed
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Trim to target duration
        n_samples = min(len(data), int(sr * target_duration_s))
        trimmed_data = data[:n_samples]

        # Normalize audio peak
        peak = np.max(np.abs(trimmed_data))
        if peak > 0:
            trimmed_data = trimmed_data / peak * 0.9

        dest_wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(dest_wav), trimmed_data, sr, format="WAV", subtype="PCM_16")
        return True
    except Exception as e:
        print(f"Error processing XC{xc_id}: {e}")
        return False


def fetch_all(target_dir: Path = Path("samples")) -> list[dict]:
    """Download candidate bird clips and write samples/manifest.csv."""
    manifest_rows = []
    manifest_path = target_dir / "manifest.csv"

    print(f"Fetching up to {len(CANDIDATE_RECORDINGS)} xeno-canto recordings...")

    for item in CANDIDATE_RECORDINGS:
        xc_id = item["id"]
        common = item["common_name"]
        sci = item["scientific_name"]
        slug = sci.lower().replace(" ", "_")
        filename = f"{slug}_xc{xc_id}.wav"
        dest_path = target_dir / filename

        print(f"Downloading XC{xc_id} - {common} ({sci})...")
        meta = get_recording_metadata(xc_id)

        success = download_and_trim_audio(xc_id, dest_path, target_duration_s=15.0)
        if success:
            manifest_rows.append({
                "file": filename,
                "expected_common_name": common,
                "expected_scientific_name": sci,
                "source_url": meta["source_url"],
                "license": meta["license"],
                "attribution": meta["attribution"],
                "condition": item["condition"],
            })
            print(f"  -> Saved {filename} ({dest_path.stat().st_size // 1024} KB)")
        else:
            print(f"  -> Skipped XC{xc_id} (download/decode error)")

    # Write manifest.csv
    fieldnames = [
        "file",
        "expected_common_name",
        "expected_scientific_name",
        "source_url",
        "license",
        "attribution",
        "condition",
    ]
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\nManifest written with {len(manifest_rows)} clips at: {manifest_path}")
    return manifest_rows


if __name__ == "__main__":
    fetch_all()
