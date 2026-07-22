from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.plant import Plant 
from app.schemas.plants import PlantCreate, PlantResponse, PlantUpdate 

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
    # Convert Pydantic model to dictionary and unpack
    plant = Plant(**plant_in.model_dump())

    # Add to DB
    db.add(plant)
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
