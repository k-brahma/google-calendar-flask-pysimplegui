"""Shared helpers for demo plan templates."""

from datetime import datetime, timedelta

from core.constants import JST


REQUIRED_DEMO_PLAN_FIELDS = (
    "slot_key",
    "day_offset",
    "assignee",
    "summary",
    "location",
    "description",
    "start_hour",
    "start_minute",
    "duration_minutes",
)


def normalize_demo_plan_template(row):
    """Normalize a raw plan row into the internal template format.

    :param row: Raw row from CSV or spreadsheet.
    :type row: dict
    :return: Normalized template.
    :rtype: dict
    """
    missing_fields = [field for field in REQUIRED_DEMO_PLAN_FIELDS if str(row.get(field, "")).strip() == ""]
    if missing_fields:
        raise ValueError(f"必須項目が不足しています: {', '.join(missing_fields)}")

    return {
        "slot_key": str(row["slot_key"]).strip(),
        "day_offset": int(str(row["day_offset"]).strip()),
        "assignee": str(row["assignee"]).strip(),
        "summary": str(row["summary"]).strip(),
        "location": str(row["location"]).strip(),
        "description": str(row["description"]).strip(),
        "start_hour": int(str(row["start_hour"]).strip()),
        "start_minute": int(str(row["start_minute"]).strip()),
        "duration_minutes": int(str(row["duration_minutes"]).strip()),
    }


def build_demo_plans(plan_templates, base_date=None):
    """Build dated demo plans from normalized templates.

    :param plan_templates: Demo templates.
    :type plan_templates: list[dict]
    :param base_date: Base date used for the generated schedule.
    :type base_date: datetime.date | None
    :return: Planned demo schedule rows.
    :rtype: list[dict]
    """
    if base_date is None:
        base_date = datetime.now(JST).date()

    plans = []
    for template in plan_templates:
        target_date = base_date + timedelta(days=template["day_offset"])
        start_at = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            template["start_hour"],
            template["start_minute"],
            tzinfo=JST,
        )
        end_at = start_at + timedelta(minutes=template["duration_minutes"])
        plans.append(
            {
                **template,
                "target_date": target_date,
                "start_at": start_at,
                "end_at": end_at,
                "weekday_label": ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()],
                "planned_time_label": f"{start_at.strftime('%Y-%m-%d %H:%M')} - {end_at.strftime('%H:%M')}",
            }
        )

    return plans
