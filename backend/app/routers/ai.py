from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.plant import Plant
from app.schemas.care_guide import (
    CarePreviewRequest,
    CareGuideResponse,
    ChatRequest,
    ChatResponse,
    HealthCheckRequest,
    HealthCheckResponse,
)
from app.schemas.identify import PlantIdentification
from app.services.gemini import generate_json


# Small helper used by every endpoint in this router.
def get_plant_or_404(plant_id: int, db: Session) -> Plant:
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


# AI endpoints are the `/plants` prefix.
router = APIRouter(prefix="/plants", tags=["ai"])


# Identify a plant from an uploaded photo (no DB write)
@router.post("/identify", response_model=PlantIdentification)
async def identify_plant(image: UploadFile = File(...)):
    content_type = (image.content_type or "").lower()
    if content_type not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
        raise HTTPException(
                status_code=400,
                detail="Unsupported image type. Use JPEG, PNG, or WebP.",
                )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload.")

    prompt = """
You are Sprout, a plant identification assistant for beginners.
Return ONLY valid JSON that matches the given schema.

Task:
- Identify the plant in the photo.
- Set is_plant to false if the image is not a plant.
- Provide a confidence score between 0 and 1.
- Optionally include a few alternative species guesses.
- Optionally suggest a high-level light_requirement.
""".strip()

    return generate_json(
            prompt=prompt,
            response_model=PlantIdentification,
            image_bytes=image_bytes,
            image_mime_type=content_type if content_type != "image/jpg" else "image/jpeg",
            )


# Generate care data before a plant is saved
@router.post("/care-preview", response_model=CareGuideResponse)
def care_preview(payload: CarePreviewRequest):
    name = payload.name or payload.species

    prompt = f"""
You are Sprout, a plant care assistant for beginners.
Return ONLY valid JSON that matches the given schema.

Plant:
- name: {name}
- species: {payload.species}

Task:
Generate a practical care guide with:
- watering_schedule
- fertilizing
- repotting

Constraints:
- Keep it beginner-friendly and safe.
- Be specific (numbers, intervals, step-by-step).
""".strip()

    return generate_json(prompt=prompt, response_model=CareGuideResponse)


# Generate a care guide for a plant (watering, fertilizing, repotting)
@router.post("/{plant_id}/care-guide", response_model=CareGuideResponse)
def care_guide(plant_id: int, db: Session = Depends(get_db)):
    plant = get_plant_or_404(plant_id, db)

    # We always ask for JSON only because `generate_json()` will validate the
    # response against the Pydantic schema (CareGuideResponse).
    prompt = f"""
You are Sprout, a plant care assistant for beginners.
Return ONLY valid JSON that matches the given schema.

Plant:
- name: {plant.nickname}
- species: {plant.species}
- location: {plant.location or "unknown"}
- watering_interval_days (current app setting): {plant.watering_interval_days}
- light_requirement: {plant.light_requirement or "unknown"}

Task:
Generate a practical care guide with:
- watering_schedule
- fertilizing
- repotting

Constraints:
- Keep it beginner-friendly and safe.
- Be specific (numbers, intervals, step-by-step).
""".strip()

    return generate_json(prompt=prompt, response_model=CareGuideResponse)


# Symptom -> health check guidance
@router.post("/{plant_id}/health-check", response_model=HealthCheckResponse)
def health_check(plant_id: int, payload: HealthCheckRequest, db: Session = Depends(get_db)):
    plant = get_plant_or_404(plant_id, db)

    # For now this is text-only. Later we can add an image upload and pass both.
    prompt = f"""
You are Sprout, a plant care assistant.
Return ONLY valid JSON that matches the given schema.

Plant:
- name: {plant.nickname}
- species: {plant.species}
- location: {plant.location or "unknown"}
- light_requirement: {plant.light_requirement or "unknown"}
- watering_interval_days: {plant.watering_interval_days}
- last_watered_at: {plant.last_watered_at or "unknown"}

User symptoms:
{payload.symptoms}

Extra signals:
- soil_moisture: {payload.soil_moisture or "unknown"}
- light: {payload.light or "unknown"}
- last_watered_at (user): {payload.last_watered_at or "unknown"}

Task:
Provide a short triage: urgency, likely causes with confidence, and recommended actions.

Safety:
- If you suspect pests/mold/rot, include a "stop_if" caution where relevant.
- No medical advice. Plant care only.
""".strip()

    return generate_json(prompt=prompt, response_model=HealthCheckResponse)


# Chat endpoint (plant-specific assistant)
@router.post("/{plant_id}/chat", response_model=ChatResponse)
def chat(plant_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    plant = get_plant_or_404(plant_id, db)

    # Flatten messages into a simple transcript for now (easy + model-agnostic).
    transcript_lines = []
    for m in payload.messages:
        transcript_lines.append(f"{m.role.upper()}: {m.content}")
    transcript = "\n".join(transcript_lines).strip()

    prompt = f"""
You are Sprout, a helpful plant care assistant for beginners.
Return ONLY valid JSON that matches the given schema.

Plant:
- name: {plant.nickname}
- species: {plant.species}
- location: {plant.location or "unknown"}
- light_requirement: {plant.light_requirement or "unknown"}
- watering_interval_days: {plant.watering_interval_days}
- last_watered_at: {plant.last_watered_at or "unknown"}

Conversation:
{transcript}

Task:
- Write the next assistant reply in plain text (no markdown).
- Optionally include 0-5 suggested next actions.
""".strip()

    return generate_json(prompt=prompt, response_model=ChatResponse, temperature=0.4)

