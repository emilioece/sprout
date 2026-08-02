from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


# One care guide per plant — scalar fields from CareGuideResponse
class PlantCareGuide(Base):
    __tablename__ = "plant_care_guides"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False, unique=True)

    # Watering
    watering_interval_days = Column(Integer, nullable=False)
    watering_method_summary = Column(Text, nullable=False)

    # Fertilizing
    fertilizing_interval_days = Column(Integer, nullable=False)
    fertilizer_type = Column(String, nullable=False)
    dilution_or_strength = Column(String, nullable=False)

    # Repotting
    repotting_interval_months = Column(Integer, nullable=False)
    best_season = Column(String, nullable=False)
    pot_size_change = Column(String, nullable=False)

    created_at = Column(
            DateTime,
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
            )

    plant = relationship("Plant", back_populates="care_guide")
    items = relationship(
            "PlantCareGuideItem",
            back_populates="care_guide",
            cascade="all, delete-orphan",
            )


# List fields from CareGuideResponse (how_to_check, soil_mix, steps, etc.)
class PlantCareGuideItem(Base):
    __tablename__ = "plant_care_guide_items"
    __table_args__ = (
            UniqueConstraint(
                    "care_guide_id",
                    "section",
                    "kind",
                    "position",
                    name="uq_care_guide_item_slot",
                    ),
            )

    id = Column(Integer, primary_key=True, index=True)
    care_guide_id = Column(
            Integer,
            ForeignKey("plant_care_guides.id"),
            nullable=False,
            )

    # e.g. watering | fertilizing | repotting
    section = Column(String, nullable=False)
    # e.g. how_to_check_if_due | soil_mix | step_by_step
    kind = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)

    care_guide = relationship("PlantCareGuide", back_populates="items")
