from datetime import datetime 
from pydantic import BaseModel 

# Request model used when adding a new plant
class PlantCreate(BaseModel):
    species: str
    nickname: str
    location: str | None = None
    watering_interval_days: int = 7
    light_requirement: str | None = None

# Request model used when updating an existing plant
class PlantUpdate(BaseModel):
    species: str | None = None 
    nickname: str| None = None
    location: str | None = None
    watering_interval_days: int | None = None
    light_requirement: str | None = None
    last_watered_at: datetime | None = None


# Response model returned by API
class PlantResponse(BaseModel):
    id: int
    nickname: str
    species: str
    location: str | None
    watering_interval_days: int
    light_requirement: str | None
    last_watered_at: datetime | None
    created_at: datetime


    class Config:
        from_attributes = True
