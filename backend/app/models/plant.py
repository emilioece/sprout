from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key= True, index = True)

    # Plant information 
    species  =  Column(String,  nullable=False)
    nickname  =  Column(String,  nullable=False)
    location =  Column(String,  nullable= True)


    # Care information 
    watering_interval_days = Column(Integer, nullable = False, default = 7)
    light_requirement = Column(String, nullable = True)


    # History
    last_watered_at = Column(DateTime, nullable = True)

    # On creation, date should exist
    created_at = Column(
            DateTime, 
            nullable=False, 
            default= lambda: datetime.now(timezone.utc))

