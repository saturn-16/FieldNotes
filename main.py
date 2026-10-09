"""FastAPI backend for Field Notes - Offline-First Birding Companion."""

from datetime import datetime
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from fieldnotes.config import (
    DB_PATH,
    DEFAULT_CONFIDENCE,
    DEFAULT_MODEL,
    get_available_ollama_models,
)
from fieldnotes.detector import detect
from fieldnotes.journal import generate_entry
from fieldnotes.lifelist import (
    add_sightings,
    get_db_connection,
    get_life_list,
    init_db,
    weekly_progress,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

from contextlib import asynccontextmanager


def init_journal_db(db_path: Path | str = DB_PATH) -> None:
    """Ensure journal_entries table exists in SQLite database."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                place TEXT,
                content TEXT NOT NULL,
                markdown TEXT NOT NULL
            )
            """
        )
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_journal_db(DB_PATH)
    yield


app = FastAPI(
    title="Field Notes API",
    description="Offline-first birding companion backend",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static directory if index.html or other static files exist
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def get_index():
    """Serve the static single-page application."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": "static/index.html not found"},
        )
    return FileResponse(str(index_file))


@app.get("/api/models")
def get_models():
    """List locally available Ollama models."""
    models = get_available_ollama_models()
    return {
        "models": models,
        "default": DEFAULT_MODEL if (DEFAULT_MODEL in models or not models) else models[0],
    }


@app.post("/api/identify")
async def identify_birds(
    audio: UploadFile = File(...),
    place: Optional[str] = Form(None),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    min_confidence: float = Form(DEFAULT_CONFIDENCE),
    model: Optional[str] = Form(None),
):
    """Analyze bird audio with BirdNET and generate an LLM field journal entry."""
    content = await audio.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    target_model = model.strip() if model and model.strip() else DEFAULT_MODEL

    # Verify model availability if Ollama models can be checked
    available_models = get_available_ollama_models()
    if available_models and target_model not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Ollama model '{target_model}' is not pulled locally. Run 'ollama pull {target_model}'.",
        )

    # Save audio temporarily for BirdNET
    filename = audio.filename or "audio.wav"
    suffix = Path(filename).suffix or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(content)
        tmp_audio_path = tmp_file.name

    try:
        observation_time = datetime.now()
        week_num = observation_time.isocalendar()[1]

        # Run BirdNET detection
        try:
            detections = detect(
                audio_path=tmp_audio_path,
                lat=lat,
                lon=lon,
                week=week_num,
                min_confidence=min_confidence,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing audio with BirdNET: {e}",
            )

        # Log sightings in life list
        new_species = add_sightings(
            detections=detections,
            place=place,
            when=observation_time,
            db_path=DB_PATH,
        )

        # Generate journal entry with Ollama
        journal_text = generate_entry(
            detections=detections,
            place=place,
            when=observation_time,
            model=target_model,
        )

        if journal_text.startswith("Error: Unable to connect to Ollama"):
            raise HTTPException(
                status_code=503,
                detail="Ollama isn't running. Please start Ollama locally ('ollama serve') and try again.",
            )
        if journal_text.startswith("Error from Ollama"):
            raise HTTPException(
                status_code=400,
                detail=journal_text,
            )

        # Format Markdown for export
        date_str = observation_time.strftime("%B %d, %Y at %I:%M %p")
        place_str = place.strip() if place and place.strip() else "The Field"
        detections_md = (
            "\n".join(
                f"- **{d.common_name}** (*{d.scientific_name}*) — {d.confidence:.0%} confidence"
                for d in detections
            )
            if detections
            else "None detected"
        )

        markdown_content = (
            f"# 🌿 Field Notes Journal Entry\n\n"
            f"**Date:** {date_str}  \n"
            f"**Location:** {place_str}\n\n"
            f"## Detected Species\n"
            f"{detections_md}\n\n"
            f"## Journal Notes\n"
            f"{journal_text}\n"
        )

        # Persist entry in database for export
        init_journal_db(DB_PATH)
        conn = get_db_connection(DB_PATH)
        with conn:
            cur = conn.execute(
                """
                INSERT INTO journal_entries (created_at, place, content, markdown)
                VALUES (?, ?, ?, ?)
                """,
                (
                    observation_time.isoformat(),
                    place_str,
                    journal_text,
                    markdown_content,
                ),
            )
            entry_id = cur.lastrowid
        conn.close()

        detections_json = [
            {
                "common_name": d.common_name,
                "scientific_name": d.scientific_name,
                "confidence": round(d.confidence, 4),
                "start_s": round(d.start_s, 2),
                "end_s": round(d.end_s, 2),
            }
            for d in detections
        ]

        return {
            "detections": detections_json,
            "journal": journal_text,
            "new_species": new_species,
            "entry_id": entry_id,
        }

    finally:
        if os.path.exists(tmp_audio_path):
            os.remove(tmp_audio_path)


@app.get("/api/lifelist")
def api_lifelist():
    """Retrieve full life list."""
    rows = get_life_list(db_path=DB_PATH)
    return [
        {
            "common_name": r["common_name"],
            "scientific_name": r["scientific_name"],
            "first_seen": r["first_seen"],
            "place": r["place"],
            "note": r["note"],
        }
        for r in rows
    ]


@app.get("/api/weekly")
def api_weekly(goal: int = 5):
    """Retrieve weekly goal progress."""
    count, goal_val = weekly_progress(goal=goal, db_path=DB_PATH)
    return {
        "count": count,
        "goal": goal_val,
    }


@app.get("/api/export/{entry_id}")
def export_entry(entry_id: int):
    """Download a journal entry formatted as Markdown."""
    init_journal_db(DB_PATH)
    conn = get_db_connection(DB_PATH)
    cur = conn.execute(
        "SELECT markdown FROM journal_entries WHERE id = ?",
        (entry_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Journal entry not found.")

    markdown_text = row["markdown"]
    filename = f"field_notes_entry_{entry_id}.md"

    return Response(
        content=markdown_text,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

