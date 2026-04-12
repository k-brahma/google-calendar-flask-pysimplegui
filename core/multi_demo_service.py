"""Services for the /multi sales demo page."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.constants import JST, MULTI_DEMO_SESSION_KEY, MULTI_DEMO_SLOT_MARKER


def build_multi_demo_plans(base_date=None):
    """Return fixed demo plans for the sales scenario.

    :param base_date: Base date used for the generated schedule.
    :type base_date: datetime.date | None
    :return: Planned demo schedule rows.
    :rtype: list[dict]
    """
    if base_date is None:
        base_date = datetime.now(JST).date()

    plan_templates = [
        {
            "slot_key": "sales-demo-1",
            "day_offset": 1,
            "assignee": "営業担当Aさん",
            "summary": "○○商事訪問",
            "location": "○○商事 本社会議室",
            "description": "基幹システム刷新に向けた初回訪問。現場責任者へデモを実施する。",
            "start_hour": 10,
            "start_minute": 0,
            "duration_minutes": 120,
        },
        {
            "slot_key": "sales-demo-2",
            "day_offset": 1,
            "assignee": "営業担当Aさん",
            "summary": "△□建設訪問",
            "location": "△□建設 東京支店",
            "description": "工事進捗共有の運用課題をヒアリングし、導入プランを提案する。",
            "start_hour": 13,
            "start_minute": 30,
            "duration_minutes": 120,
        },
        {
            "slot_key": "sales-demo-3",
            "day_offset": 2,
            "assignee": "営業担当Bさん",
            "summary": "青葉食品訪問",
            "location": "青葉食品 開発センター",
            "description": "品質管理部門への提案前ヒアリング。帳票電子化ニーズを確認する。",
            "start_hour": 9,
            "start_minute": 30,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-4",
            "day_offset": 2,
            "assignee": "営業担当Cさん",
            "summary": "東西物流 オンライン商談",
            "location": "オンライン商談",
            "description": "倉庫別の在庫可視化について、部門長向けの提案デモを実施する。",
            "start_hour": 11,
            "start_minute": 0,
            "duration_minutes": 60,
        },
        {
            "slot_key": "sales-demo-5",
            "day_offset": 2,
            "assignee": "営業担当Cさん",
            "summary": "星野メディカル訪問",
            "location": "星野メディカル 横浜オフィス",
            "description": "展示会リードのフォロー訪問。電子カルテ連携の関心度を確認する。",
            "start_hour": 14,
            "start_minute": 30,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-6",
            "day_offset": 3,
            "assignee": "営業担当Aさん",
            "summary": "第一設備訪問",
            "location": "第一設備 千葉営業所",
            "description": "見積提示前の現場確認。保守契約を含めた提案条件を整理する。",
            "start_hour": 10,
            "start_minute": 30,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-7",
            "day_offset": 3,
            "assignee": "営業担当Bさん",
            "summary": "みなと産業訪問",
            "location": "みなと産業 本社",
            "description": "導入後の活用イメージを役員層へ説明し、稟議前の疑問点を解消する。",
            "start_hour": 13,
            "start_minute": 30,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-8",
            "day_offset": 4,
            "assignee": "営業担当Cさん",
            "summary": "日の出不動産訪問",
            "location": "日の出不動産 渋谷本店",
            "description": "営業進捗管理の改善提案。店舗責任者向けに画面デモを行う。",
            "start_hour": 10,
            "start_minute": 0,
            "duration_minutes": 120,
        },
        {
            "slot_key": "sales-demo-9",
            "day_offset": 4,
            "assignee": "営業担当Aさん",
            "summary": "西東京サービス訪問",
            "location": "西東京サービス 立川支社",
            "description": "既存顧客の追加提案。部門別権限設定の要望を確認する。",
            "start_hour": 14,
            "start_minute": 0,
            "duration_minutes": 60,
        },
        {
            "slot_key": "sales-demo-10",
            "day_offset": 5,
            "assignee": "営業担当Bさん",
            "summary": "双葉工業訪問",
            "location": "双葉工業 研究棟",
            "description": "契約前最終面談。導入スケジュールと初期設定範囲を詰める。",
            "start_hour": 10,
            "start_minute": 0,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-11",
            "day_offset": 5,
            "assignee": "営業担当Cさん",
            "summary": "高砂ソリューション訪問",
            "location": "高砂ソリューション 品川ラボ",
            "description": "PoC結果報告と次回提案準備。技術部門との認識合わせを行う。",
            "start_hour": 13,
            "start_minute": 30,
            "duration_minutes": 90,
        },
        {
            "slot_key": "sales-demo-12",
            "day_offset": 5,
            "assignee": "営業担当Aさん",
            "summary": "中央商会訪問",
            "location": "中央商会 役員応接室",
            "description": "最終提案のクロージング。契約条件と社内展開計画を確認する。",
            "start_hour": 16,
            "start_minute": 0,
            "duration_minutes": 60,
        },
    ]

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


def build_multi_demo_description(plan):
    """Build the description text for a demo event.

    :param plan: Demo plan row.
    :type plan: dict
    :return: Event description.
    :rtype: str
    """
    return "\n".join(
        [
            "営業デモ用の自動生成イベントです。",
            f"担当: {plan['assignee']}",
            f"想定内容: {plan['description']}",
            f"{MULTI_DEMO_SLOT_MARKER}{plan['slot_key']}",
        ]
    )


def extract_multi_demo_slot_key(description):
    """Extract the demo slot key from an event description.

    :param description: Event description.
    :type description: str
    :return: Slot key or ``None``.
    :rtype: str | None
    """
    if not description:
        return None

    for line in description.splitlines():
        if line.startswith(MULTI_DEMO_SLOT_MARKER):
            return line.replace(MULTI_DEMO_SLOT_MARKER, "", 1).strip()

    return None


def get_multi_demo_session_ids(session_obj):
    """Read demo event ids from the session.

    :param session_obj: Flask session object.
    :return: Slot key to event id mapping.
    :rtype: dict
    """
    event_ids = session_obj.get(MULTI_DEMO_SESSION_KEY, {})
    if isinstance(event_ids, dict):
        return event_ids.copy()
    return {}


def save_multi_demo_session_ids(session_obj, event_ids):
    """Persist demo event ids in the session.

    :param session_obj: Flask session object.
    :param event_ids: Slot key to event id mapping.
    """
    session_obj[MULTI_DEMO_SESSION_KEY] = event_ids
    session_obj.modified = True


def clear_multi_demo_session_ids(session_obj):
    """Remove demo event ids from the session.

    :param session_obj: Flask session object.
    """
    session_obj.pop(MULTI_DEMO_SESSION_KEY, None)
    session_obj.modified = True


def format_event_datetime_for_display(event_time):
    """Format an event time for the UI.

    :param event_time: Google Calendar event time block.
    :type event_time: dict | None
    :return: Formatted time label.
    :rtype: str
    """
    if not event_time:
        return "-"

    if event_time.get("dateTime"):
        dt = datetime.fromisoformat(event_time["dateTime"].replace("Z", "+00:00"))
        return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M")

    if event_time.get("date"):
        return event_time["date"]

    return "-"


def format_demo_description_for_display(description):
    """Remove internal marker lines from a demo description.

    :param description: Raw event description.
    :type description: str | None
    :return: Description suitable for the UI.
    :rtype: str
    """
    if not description:
        return "-"

    lines = []
    for line in description.splitlines():
        if line.startswith(MULTI_DEMO_SLOT_MARKER):
            continue
        lines.append(line)

    return "\n".join(lines).strip() or "-"


def list_future_events(calendar_manager, start_time=None):
    """Fetch all future events using pagination.

    :param calendar_manager: Calendar manager instance.
    :param start_time: Lower bound time.
    :type start_time: datetime | None
    :return: Future events.
    :rtype: list[dict]
    """
    if start_time is None:
        start_time = datetime.now(JST)

    time_min = start_time.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    events = []
    page_token = None

    while True:
        params = {
            "calendarId": calendar_manager.target_calendar_id,
            "timeMin": time_min,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 2500,
        }
        if page_token:
            params["pageToken"] = page_token

        result = calendar_manager.service.events().list(**params).execute()
        events.extend(result.get("items", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return events


def load_multi_demo_event_lookup(calendar_manager, session_obj, plans):
    """Resolve demo plans to actual Google Calendar events.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Flask session object.
    :param plans: Demo plans.
    :type plans: list[dict]
    :return: Slot key to event mapping.
    :rtype: dict
    """
    session_ids = get_multi_demo_session_ids(session_obj)
    event_lookup = {}

    for plan in plans:
        event_id = session_ids.get(plan["slot_key"])
        if not event_id:
            continue

        event = calendar_manager.get_event(event_id)
        if event:
            event_lookup[plan["slot_key"]] = event
        else:
            session_ids.pop(plan["slot_key"], None)

    future_events = list_future_events(calendar_manager)
    for event in future_events:
        slot_key = extract_multi_demo_slot_key(event.get("description", ""))
        if not slot_key or slot_key in event_lookup:
            continue

        event_lookup[slot_key] = event
        if event.get("id"):
            session_ids[slot_key] = event["id"]

    save_multi_demo_session_ids(session_obj, session_ids)
    return event_lookup


def build_multi_demo_rows(calendar_manager, session_obj):
    """Build UI rows for the /multi page.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Flask session object.
    :return: UI rows.
    :rtype: list[dict]
    """
    plans = build_multi_demo_plans()
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
                    event.get("summary", "") != f"[営業デモ] {plan['assignee']} | {plan['summary']}",
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
                "status_label": "作成済み" if event else "未作成",
                "actual_summary": event.get("summary", "-") if event else "-",
                "actual_location": event.get("location", "-") if event else "-",
                "actual_start": actual_start,
                "actual_end": actual_end,
                "actual_description": format_demo_description_for_display(actual_description),
                "has_changes": has_changes,
            }
        )

    return rows


def create_multi_demo_events(calendar_manager, session_obj):
    """Create missing demo events in bulk.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Flask session object.
    :return: Created count, skipped count, failed summaries.
    :rtype: tuple[int, int, list[str]]
    """
    plans = build_multi_demo_plans()
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
            summary=f"[営業デモ] {plan['assignee']} | {plan['summary']}",
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


def flush_future_events(calendar_manager, session_obj):
    """Delete all future events in the target calendar.

    :param calendar_manager: Calendar manager instance.
    :param session_obj: Flask session object.
    :return: Deleted count and failed count.
    :rtype: tuple[int, int]
    """
    deleted_count = 0
    failed_count = 0

    for event in list_future_events(calendar_manager):
        event_id = event.get("id")
        if not event_id:
            failed_count += 1
            continue

        if calendar_manager.delete_event(event_id):
            deleted_count += 1
        else:
            failed_count += 1

    clear_multi_demo_session_ids(session_obj)
    return deleted_count, failed_count
