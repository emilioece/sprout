import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.plant import Plant 
from app.schemas.plants import PlantCreate, PlantResponse, PlantUpdate 
from app.services.care_guide_mapper import care_guide_to_orm

# Photos are saved here and served back out at /uploads/<filename>
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# Helper function to query plant
def get_plant_or_404(plant_id:int, db: Session) -> Plant:
    # Start query 
    query  = db.query(Plant)

    # Filter for requested plant ID 
    query  = query.filter(Plant.id == plant_id)

    # Return the first matching plant
    plant = query.first()

    # If plant_id not found, return exception, else return plant
    if not plant:
        raise HTTPException(status_code = 404, detail = "Plant not found")

    return plant
    


# Configure plant-related API endpoints
router = APIRouter(prefix = "/plants", tags = ["plants"])

@router.get("/", response_model = list[PlantResponse])
def list_plants(db: Session = Depends(get_db)):
    return db.query(Plant).all()

@router.post("/", response_model = PlantResponse, status_code= 201)
def create_plant(plant_in: PlantCreate, db: Session = Depends(get_db)):
    # Convert Pydantic model to dictionary and unpack (care_guide is related tables)
    plant = Plant(**plant_in.model_dump(exclude={"care_guide"}))

    if plant_in.care_guide is not None:
        plant.watering_interval_days = (
                plant_in.care_guide.watering_schedule.interval_days
                )

    # Add to DB
    db.add(plant)
    # Assign plant.id before inserting the related care guide row
    db.flush()

    if plant_in.care_guide is not None:
        db.add(care_guide_to_orm(plant.id, plant_in.care_guide))

    db.commit()

    # Reload DB
    db.refresh(plant)

    return plant

@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id:int, db: Session = Depends(get_db)):
    return get_plant_or_404(plant_id, db)

@router.put("/{plant_id}", response_model = PlantResponse)
def update_plant(plant_id:int, plant_in: PlantUpdate, db: Session = Depends(get_db)):
    # Find plant or return 404
    plant = get_plant_or_404(plant_id, db)

    # Update changed fields and leave the rest unchanged
    update_data = plant_in.model_dump(exclude_unset = True)

    # Set changed attributes to Plant
    for field, value in  update_data.items():
        setattr(plant, field, value)

    #  Update changes on DB
    db.commit()
    db.refresh(plant)

    return plant

@router.delete("/{plant_id}", status_code = 204)
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = get_plant_or_404(plant_id, db)

    db.delete(plant)
    db.commit()
    
    return None

# Update a plant's last watered timestamp to current UTC time.
@router.post("/{plant_id}/water", response_model=PlantResponse)
def water_plant(plant_id:int, db: Session = Depends(get_db)):
    plant = get_plant_or_404(plant_id, db)

    plant.last_watered_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(plant)

    return plant

# Upload/replace a plant's photo. Saves the file to disk and stores
@router.post("/{plant_id}/photo", response_model=PlantResponse)
def upload_plant_photo(
    plant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    plant = get_plant_or_404(plant_id, db)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPEG, PNG, or WEBP.",
        )

    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB).")

    # Remove the old photo file, if there was one, so we don't
    # accumulate orphaned uploads every time a plant's photo changes.
    if plant.photo_url:
        old_path = os.path.join(UPLOAD_DIR, os.path.basename(plant.photo_url))
        if os.path.exists(old_path):
            os.remove(old_path)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"plant_{plant_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    plant.photo_url = f"/uploads/{filename}"

    db.commit()
    db.refresh(plant)

    return plant