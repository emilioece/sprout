from app.models.care_guide import PlantCareGuide, PlantCareGuideItem
from app.schemas.care_guide import (
    CareGuideResponse,
    FertilizingPlan,
    RepottingGuide,
    WateringSchedule,
)


# (section, kind) -> attribute path on CareGuideResponse for list fields
_LIST_FIELDS = (
    ("watering", "how_to_check_if_due"),
    ("watering", "signs_underwatering"),
    ("watering", "signs_overwatering"),
    ("watering", "seasonal_adjustments"),
    ("fertilizing", "when_to_pause"),
    ("fertilizing", "cautions"),
    ("repotting", "signs_need_repotting"),
    ("repotting", "soil_mix"),
    ("repotting", "step_by_step"),
    ("repotting", "aftercare"),
)


def _section_model(guide: CareGuideResponse, section: str):
    if section == "watering":
        return guide.watering_schedule
    if section == "fertilizing":
        return guide.fertilizing
    return guide.repotting


# Build ORM rows from a CareGuideResponse (not committed)
def care_guide_to_orm(plant_id: int, guide: CareGuideResponse) -> PlantCareGuide:
    row = PlantCareGuide(
            plant_id=plant_id,
            watering_interval_days=guide.watering_schedule.interval_days,
            watering_method_summary=guide.watering_schedule.method_summary,
            fertilizing_interval_days=guide.fertilizing.interval_days,
            fertilizer_type=guide.fertilizing.fertilizer_type,
            dilution_or_strength=guide.fertilizing.dilution_or_strength,
            repotting_interval_months=guide.repotting.interval_months,
            best_season=guide.repotting.best_season,
            pot_size_change=guide.repotting.pot_size_change,
            )

    items = []
    for section, kind in _LIST_FIELDS:
        values = getattr(_section_model(guide, section), kind)
        for position, text in enumerate(values):
            items.append(
                    PlantCareGuideItem(
                            section=section,
                            kind=kind,
                            position=position,
                            text=text,
                            )
                    )
    row.items = items
    return row


def _texts_for(items: list[PlantCareGuideItem], section: str, kind: str) -> list[str]:
    matched = [i for i in items if i.section == section and i.kind == kind]
    matched.sort(key=lambda i: i.position)
    return [i.text for i in matched]


# Rebuild CareGuideResponse from stored ORM rows
def care_guide_to_response(
        row: PlantCareGuide,
        *,
        name: str,
        species: str,
        ) -> CareGuideResponse:
    items = list(row.items or [])

    return CareGuideResponse(
            name=name,
            species=species,
            watering_schedule=WateringSchedule(
                    interval_days=row.watering_interval_days,
                    method_summary=row.watering_method_summary,
                    how_to_check_if_due=_texts_for(items, "watering", "how_to_check_if_due"),
                    signs_underwatering=_texts_for(items, "watering", "signs_underwatering"),
                    signs_overwatering=_texts_for(items, "watering", "signs_overwatering"),
                    seasonal_adjustments=_texts_for(items, "watering", "seasonal_adjustments"),
                    ),
            fertilizing=FertilizingPlan(
                    interval_days=row.fertilizing_interval_days,
                    fertilizer_type=row.fertilizer_type,
                    dilution_or_strength=row.dilution_or_strength,
                    when_to_pause=_texts_for(items, "fertilizing", "when_to_pause"),
                    cautions=_texts_for(items, "fertilizing", "cautions"),
                    ),
            repotting=RepottingGuide(
                    interval_months=row.repotting_interval_months,
                    best_season=row.best_season,
                    signs_need_repotting=_texts_for(items, "repotting", "signs_need_repotting"),
                    pot_size_change=row.pot_size_change,
                    soil_mix=_texts_for(items, "repotting", "soil_mix"),
                    step_by_step=_texts_for(items, "repotting", "step_by_step"),
                    aftercare=_texts_for(items, "repotting", "aftercare"),
                    ),
            )
