from __future__ import annotations

from pydantic import BaseModel, Field


class PlantAlternative(BaseModel):
    species: str = Field(description="Alternate species guess.")
    confidence: float = Field(ge=0.0, le=1.0)


# Gemini vision response for a plant photo
class PlantIdentification(BaseModel):
    species: str = Field(description="Best-guess common or scientific name")
    confidence: float = Field(ge=0.0, le=1.0)

    is_plant: bool = Field(
        default=True,
        description="False if the image does not appear to be a plant.",
    )

    alternatives: list[PlantAlternative] = Field(default_factory=list)

    light_requirement: str | None = Field(
        default=None,
        description="Optional high-level light hint for PlantCreate.",
    )
