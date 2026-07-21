from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.plant import Plant 
from app.schemas.plants import PlantCreate, PlantResponse 


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
