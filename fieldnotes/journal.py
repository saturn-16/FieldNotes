"""Ollama-powered field journal entry generator."""

from datetime import datetime
import ollama

from fieldnotes.models import Detection


def generate_entry(
    detections: list[Detection],
    place: str | None,
    when: datetime,
    model: str,
) -> str:
    """Generate a short field-journal entry based on detected bird species.

    Uses only the species detected, with a friendly 4-6 sentence narrative,
    a fun fact per bird, and a 'listen for next time' tip.
    """
    location_desc = place.strip() if place and place.strip() else "the field"
    date_str = when.strftime("%B %d, %Y at %I:%M %p")

    # Graceful handling for empty detections without calling LLM
    if not detections:
        return (
            f"Field Journal - {date_str}\n"
            f"Location: {location_desc}\n\n"
            f"No clear calls this time. Keep your ears tuned and try another recording nearby!"
        )

    # Format list of species strictly
    bird_lines = [
        f"- {d.common_name} ({d.scientific_name})" for d in detections
    ]
    birds_text = "\n".join(bird_lines)

    prompt = (
        f"You are a personal field-journal assistant for a birder.\n"
        f"Observation details:\n"
        f"- Date/Time: {date_str}\n"
        f"- Location: {location_desc}\n"
        f"- Detected birds:\n{birds_text}\n\n"
        f"Instructions:\n"
        f"1. Rely ONLY on the detected species listed above. Do not invent, assume, or add any other species.\n"
        f"2. Write 4-6 friendly sentences describing the birding observation outdoors.\n"
        f"3. Provide exactly one short fun fact for each bird detected.\n"
        f"4. Provide one 'Listen for next time' tip to help the birder recognize these calls in the future.\n"
        f"Keep the tone warm, observant, and grounded in nature."
    )

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            options={
                "temperature": 0.4,
            },
        )
        content = response["message"]["content"].strip()
        return content
    except ollama.ResponseError as e:
        return (
            f"Error from Ollama ({e.status_code}): Model '{model}' may not be available or encountered an issue. "
            f"Please verify with 'ollama list' or run 'ollama pull {model}'."
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "connect" in err_msg or "connection" in err_msg or "refused" in err_msg:
            return (
                "Error: Unable to connect to Ollama service. "
                "Please verify that Ollama is running locally (e.g., 'ollama serve')."
            )
        return f"Error generating journal entry: {e}"
