"""Services for importing demo schedules from Google Spreadsheet."""

from datetime import datetime, timedelta

from core.constants import JST
from core.demo_plan_service import REQUIRED_DEMO_PLAN_FIELDS, build_demo_plans, normalize_demo_plan_template
from core.multi_demo_service import (
    build_multi_demo_description,
    format_demo_description_for_display,
    format_event_datetime_for_display,
    get_multi_demo_session_ids,
    load_multi_demo_event_lookup,
    save_multi_demo_session_ids,
)


SPREADSHEET_REQUIRED_FIELDS = (
    "slot_key",
    "day",
    "assignee",
    "summary",
    "location",
    "description",
    "start_hour",
    "start_minute",
    "duration_minutes",
)


def _build_spreadsheet_demo_row(template, target_date):
    """Build a dated spreadsheet row from a template and explicit date."""
    start_at = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        template["start_hour"],
        template["start_minute"],
        tzinfo=JST,
    )
    end_at = start_at + timedelta(minutes=template["duration_minutes"])
    return {
        **template,
        "target_date": target_date,
        "weekday_label": ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()],
        "start_at": start_at,
        "end_at": end_at,
        "planned_time_label": f"{start_at.strftime('%Y-%m-%d %H:%M')} - {end_at.strftime('%H:%M')}",
    }


def _parse_spreadsheet_day(day_value):
    """Parse the spreadsheet day value into a date."""
    value = str(day_value).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError("day は YYYY/MM/DD または YYYY-MM-DD 形式で入力してください")


def _normalize_spreadsheet_demo_plan(row, schema):
    """Normalize a spreadsheet row into the internal template format."""
    if schema == "day_offset":
        return normalize_demo_plan_template(row)

    missing_fields = [field for field in SPREADSHEET_REQUIRED_FIELDS if str(row.get(field, "")).strip() == ""]
    if missing_fields:
        raise ValueError(f"必須項目が不足しています: {', '.join(missing_fields)}")

    return {
        "slot_key": str(row["slot_key"]).strip(),
        "day": str(row["day"]).strip(),
        "target_date": _parse_spreadsheet_day(row["day"]),
        "assignee": str(row["assignee"]).strip(),
        "summary": str(row["summary"]).strip(),
        "location": str(row["location"]).strip(),
        "description": str(row["description"]).strip(),
        "start_hour": int(str(row["start_hour"]).strip()),
        "start_minute": int(str(row["start_minute"]).strip()),
        "duration_minutes": int(str(row["duration_minutes"]).strip()),
    }


def _find_header_row(values):
    """Find the first row that contains all required headers."""
    for row_index, row in enumerate(values):
        normalized_row = [str(cell).strip() for cell in row]
        if all(field in normalized_row for field in SPREADSHEET_REQUIRED_FIELDS):
            return row_index, normalized_row, "day"
        if all(field in normalized_row for field in REQUIRED_DEMO_PLAN_FIELDS):
            return row_index, normalized_row, "day_offset"

    required = ", ".join(SPREADSHEET_REQUIRED_FIELDS)
    raise ValueError(f"必要ヘッダー行が見つかりません。Spreadsheet では {required} を使用してください")


def load_demo_plans_from_spreadsheet(spreadsheet_manager):
    """Load demo plan templates from the configured spreadsheet.

    :param spreadsheet_manager: Spreadsheet manager instance.
    :return: Demo plan templates.
    :rtype: list[dict]
    """
    values = spreadsheet_manager.get_values()
    if not values:
        return []

    header_row_index, headers, schema = _find_header_row(values)
    plans = []
    required_fields = SPREADSHEET_REQUIRED_FIELDS if schema == "day" else REQUIRED_DEMO_PLAN_FIELDS

    for row_index, row in enumerate(values[header_row_index + 1 :], start=header_row_index + 2):
        padded_row = list(row) + [""] * (len(headers) - len(row))
        record = {
            header: str(padded_row[column_index]).strip()
            for column_index, header in enumerate(headers)
            if header
        }

        if not any(str(record.get(field, "")).strip() for field in required_fields):
            continue

        try:
            plans.append(_normalize_spreadsheet_demo_plan(record, schema))
        except Exception as exc:
            raise ValueError(f"{row_index}行目のデータが不正です: {exc}") from exc

    return plans


def build_spreadsheet_demo_rows(spreadsheet_manager, base_date=None):
    """Return dated demo rows loaded from Google Spreadsheet.

    :param spreadsheet_manager: Spreadsheet manager instance.
    :param base_date: Base date used for the generated schedule.
    :type base_date: datetime.date | None
    :return: Planned demo schedule rows.
    :rtype: list[dict]
    """
    plan_templates = load_demo_plans_from_spreadsheet(spreadsheet_manager)
    if not plan_templates:
        return []

    if "day" not in plan_templates[0]:
        return build_demo_plans(plan_templates, base_date=base_date)

    return [_build_spreadsheet_demo_row(template, template["target_date"]) for template in plan_templates]


def create_spreadsheet_demo_events(calendar_manager, session_obj, spreadsheet_manager):
    """Create missing calendar events from the spreadsheet schedule.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Flask session object.
    :param spreadsheet_manager: Spreadsheet manager instance.
    :return: Created count, skipped count, failed summaries.
    :rtype: tuple[int, int, list[str]]
    """
    plans = build_spreadsheet_demo_rows(spreadsheet_manager)
    event_lookup = load_multi_demo_event_lookup(calendar_manager, session_obj, plans)
    session_ids = get_multi_demo_session_ids(session_obj)
    created_count = 0
    skipped_count = 0
    failed_summaries = []

    for plan in plans:
        if event_lookup.get(plan["slot_key"]):
            skipped_count += 1
            continue

        event = calendar_manager.create_event(
            summary=f"{plan['assignee']} | {plan['summary']}",
            description=build_multi_demo_description(plan),
            location=plan["location"],
            start_time=plan["start_at"],
            end_time=plan["end_at"],
        )

        if event and event.get("id"):
            session_ids[plan["slot_key"]] = event["id"]
            created_count += 1
        else:
            failed_summaries.append(plan["summary"])

    save_multi_demo_session_ids(session_obj, session_ids)
    return created_count, skipped_count, failed_summaries


def build_spreadsheet_sync_rows(calendar_manager, session_obj, spreadsheet_manager):
    """Build spreadsheet rows merged with actual Google Calendar state.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Session-like object.
    :param spreadsheet_manager: Spreadsheet manager instance.
    :return: UI rows.
    :rtype: list[dict]
    """
    plans = build_spreadsheet_demo_rows(spreadsheet_manager)
    event_lookup = load_multi_demo_event_lookup(calendar_manager, session_obj, plans)
    rows = []

    for plan in plans:
        event = event_lookup.get(plan["slot_key"])
        actual_start = format_event_datetime_for_display(event.get("start")) if event else "-"
        actual_end = format_event_datetime_for_display(event.get("end")) if event else "-"
        actual_description = event.get("description", "-") if event else "-"
        has_changes = False

        if event:
            has_changes = any(
                [
                    event.get("summary", "") != f"{plan['assignee']} | {plan['summary']}",
                    event.get("location", "") != plan["location"],
                    actual_start != plan["start_at"].strftime("%Y-%m-%d %H:%M"),
                    actual_end != plan["end_at"].strftime("%Y-%m-%d %H:%M"),
                    actual_description != build_multi_demo_description(plan),
                ]
            )

        rows.append(
            {
                **plan,
                "event": event,
                "event_id": event.get("id") if event else None,
                "exists": bool(event),
                "actual_summary": event.get("summary", "-") if event else "-",
                "actual_location": event.get("location", "-") if event else "-",
                "actual_start": actual_start,
                "actual_end": actual_end,
                "actual_description": format_demo_description_for_display(actual_description),
                "has_changes": has_changes,
                "status_label": "Google側で編集あり" if has_changes else ("同期済み" if event else "未作成"),
            }
        )

    return rows
