# Round-trip tests for CareGuideResponse <-> ORM mapping

from app.schemas.care_guide import (
    CareGuideResponse,
    FertilizingPlan,
    RepottingGuide,
    WateringSchedule,
)
from app.services.care_guide_mapper import care_guide_to_orm, care_guide_to_response


def _sample_guide():
    return CareGuideResponse(
            name="Maria",
            species="Tagetes",
            watering_schedule=WateringSchedule(
                    interval_days=7,
                    method_summary="Water when top inch is dry",
                    how_to_check_if_due=["Finger test", "Lift pot"],
                    signs_underwatering=["Drooping leaves"],
                    signs_overwatering=["Yellow leaves"],
                    seasonal_adjustments=["Water less in winter"],
                    ),
            fertilizing=FertilizingPlan(
                    interval_days=30,
                    fertilizer_type="balanced liquid",
                    dilution_or_strength="half strength",
                    when_to_pause=["Winter", "After repotting"],
                    cautions=["Do not overfeed"],
                    ),
            repotting=RepottingGuide(
                    interval_months=12,
                    best_season="spring",
                    signs_need_repotting=["Roots circling"],
                    pot_size_change="one size up",
                    soil_mix=["potting mix", "perlite"],
                    step_by_step=["Remove plant", "Repot"],
                    aftercare=["Keep shaded for a week"],
                    ),
            )


def test_care_guide_round_trip():
    original = _sample_guide()
    row = care_guide_to_orm(plant_id=1, guide=original)
    restored = care_guide_to_response(row, name=original.name, species=original.species)

    assert restored == original
    assert row.plant_id == 1
    assert row.watering_interval_days == 7
    assert len(row.items) == 14
