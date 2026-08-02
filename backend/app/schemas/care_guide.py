"""
care_guide.py

Pydantic schemas for Gemini-powered care guidance:
- Watering schedule
- Fertilizing plan
- Repotting guide
- Symptom -> health check
- Plant-specific chat
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ===========================================================================
# Chat
# ===========================================================================

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(
        description="Who sent the message."
    )
    content: str = Field(description="Plain text content.")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(description="Conversation so far.")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional extra context (notes, preferences, etc).",
    )


class ChatResponse(BaseModel):
    reply: str = Field(description="Assistant reply for the user.")
    suggested_next_actions: list[str] = Field(
        default_factory=list,
        description="Optional follow-up actions the user can take.",
    )


# ===========================================================================
# Care guide (watering / fertilizing / repotting)
# ===========================================================================

class WateringSchedule(BaseModel):
    interval_days: int = Field(ge=1, le=60, description="Recommended baseline interval.")
    method_summary: str = Field(description="How to water (high level).")
    how_to_check_if_due: list[str] = Field(
        description="Practical checks (finger test, pot weight, etc)."
    )
    signs_underwatering: list[str] = Field(default_factory=list)
    signs_overwatering: list[str] = Field(default_factory=list)
    seasonal_adjustments: list[str] = Field(
        default_factory=list,
        description="Adjustments for season, light, humidity, etc.",
    )


class FertilizingPlan(BaseModel):
    interval_days: int = Field(ge=7, le=180, description="How often to fertilize.")
    fertilizer_type: str = Field(description="Recommended fertilizer type.")
    dilution_or_strength: str = Field(description="e.g. 'half strength'.")
    when_to_pause: list[str] = Field(
        default_factory=list,
        description="Cases to pause fertilizing (winter, after repotting, etc).",
    )
    cautions: list[str] = Field(default_factory=list)


class RepottingGuide(BaseModel):
    interval_months: int = Field(ge=3, le=60, description="How often to repot.")
    best_season: str = Field(description="Best time of year to repot.")
    signs_need_repotting: list[str] = Field(default_factory=list)
    pot_size_change: str = Field(description="How much bigger the next pot should be.")
    soil_mix: list[str] = Field(description="Suggested soil mix components.")
    step_by_step: list[str] = Field(description="Repotting steps.")
    aftercare: list[str] = Field(default_factory=list)


class CareGuideResponse(BaseModel):
    name: str = Field(description="Plant name / nickname to display.")
    species: str
    watering_schedule: WateringSchedule
    fertilizing: FertilizingPlan
    repotting: RepottingGuide


# ===========================================================================
# Care preview
# ===========================================================================

# Species-only care guide generated before the plant is saved
class CarePreviewRequest(BaseModel):
    species: str = Field(description="Species to generate a care guide for.")
    name: str | None = Field(
        default=None,
        description="Optional display name; defaults to species.",
    )


# ===========================================================================
# Symptoms -> Health check
# ===========================================================================

class HealthCheckRequest(BaseModel):
    symptoms: str = Field(description="What you see + timeline + anything tried.")
    soil_moisture: Literal["dry", "moist", "wet", "unknown"] | None = None
    light: Literal["low", "medium", "bright_indirect", "direct_sun", "unknown"] | None = None
    last_watered_at: datetime | None = None


class PossibleCause(BaseModel):
    title: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class ActionStep(BaseModel):
    title: str
    instructions: str
    when: str = Field(description="When to do it / how soon.")
    stop_if: str | None = Field(default=None, description="Safety stop condition.")


class HealthCheckResponse(BaseModel):
    urgency: Literal["low", "moderate", "urgent"]
    summary: str
    possible_causes: list[PossibleCause]
    recommended_actions: list[ActionStep]
    what_to_monitor_next: list[str] = Field(default_factory=list)
