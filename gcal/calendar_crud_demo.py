import datetime

from .calendar_manager import CalendarManager


def initialize_calendar():
    """CalendarManagerインスタンスを初期化する"""
    try:
        calendar = CalendarManager()
        print("カレンダーマネージャーの初期化成功")
        print(f"ターゲットカレンダーID: {calendar.target_calendar_id}")
        print(f"タイムゾーン: {calendar.timezone}")
        return calendar
    except Exception as e:
        print(f"カレンダーマネージャーの初期化エラー: {str(e)}")
        return None


def list_calendars():
    """利用可能なカレンダーの一覧を表示する"""
    calendar = initialize_calendar()
    if not calendar:
        return

    print("\n【カレンダーリスト取得】")
    calendars = calendar.get_calendar_list()
    if calendars:
        print(f"利用可能なカレンダー数: {len(calendars)}")
        for cal in calendars[:3]:  # 最初の3つだけ表示
            print(f"- {cal.get('summary')} ({cal.get('id')})")
        if len(calendars) > 3:
            print(f"...他 {len(calendars) - 3} 件")
    else:
        print("利用可能なカレンダーがありません")


def create_demo_event(create_meet=False):
    """デモイベントを作成する

    Args:
        create_meet: Google Meetリンク作成（現在は機能していません）
    """
    calendar = initialize_calendar()
    if not calendar:
        return None, None, None

    print("\n【イベント作成】")
    event_title = "デモイベント"
    event_description = "これはCalendarManagerクラスで作成されたデモイベントです"

    # 現在から2時間後に開始する1時間のイベント
    start_time = datetime.datetime.now() + datetime.timedelta(hours=2)
    end_time = start_time + datetime.timedelta(hours=1)

    new_event = calendar.create_event(
        summary=event_title,
        description=event_description,
        location="オンライン",
        start_time=start_time,
        end_time=end_time,
        create_meet=create_meet,
    )

    if not new_event:
        print("イベント作成に失敗しました")
        return None, None, None

    event_id = new_event.get("id")
    print(f"イベント作成成功: {new_event.get('summary')} (ID: {event_id})")
    print(f"開始時間: {calendar.format_event_time(new_event)}")

    return event_id, event_title, event_description


def read_event(event_id):
    """指定されたイベントを取得して表示する"""
    calendar = initialize_calendar()
    if not calendar:
        return None

    print("\n【イベント取得】")
    event = calendar.get_event(event_id)
    if event:
        print(f"イベント取得成功: {event.get('summary')}")
        print(f"説明: {event.get('description')}")
        return event
    else:
        print("イベント取得に失敗しました")
        return None


def update_event(event_id, event_title, event_description):
    """指定されたイベントを更新する"""
    calendar = initialize_calendar()
    if not calendar:
        return None

    print("\n【イベント更新】")
    updated_event = calendar.update_event(
        event_id=event_id,
        summary=f"{event_title} (更新済み)",
        description=f"{event_description}\n更新日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    if updated_event:
        print(f"イベント更新成功: {updated_event.get('summary')}")
        return updated_event
    else:
        print("イベント更新に失敗しました")
        return None


def list_events(max_results=5):
    """イベントリストを取得して表示する"""
    calendar = initialize_calendar()
    if not calendar:
        return

    print("\n【イベントリスト取得】")
    events = calendar.get_events(max_results=max_results)
    if events:
        print(f"今後のイベント数: {len(events)}")
        for evt in events:
            time_str = calendar.format_event_time(evt)
            print(f"- {time_str} - {evt.get('summary')}")
    else:
        print("今後のイベントはありません")


def delete_event_with_confirmation(event_id):
    """確認後、指定されたイベントを削除する"""
    calendar = initialize_calendar()
    if not calendar:
        return False

    print("\n【イベント削除】")

    # event_idからイベント情報を取得してタイトルを取得
    event = calendar.get_event(event_id)
    if not event:
        print(f"削除対象のイベントが見つかりません: {event_id}")
        return False

    event_summary = event.get("summary", "イベント")
    delete_confirm = input(f"デモイベント '{event_summary}' を削除しますか？ (y/n): ")

    if delete_confirm.lower() == "y":
        if calendar.delete_event(event_id):
            print("イベント削除成功")
            return True
        else:
            print("イベント削除に失敗しました")
            return False
    else:
        print("イベント削除をスキップしました")
        return False


def demonstrate_crud_operations(create_meet=False):
    """CalendarManagerクラスの基本的なCRUD操作をデモンストレーションする

    Args:
        create_meet: Google Meetリンク作成（現在は機能していません）
    """
    print("===== Google Calendar 操作デモ =====")

    # カレンダーリストの取得
    list_calendars()

    # イベント作成 (Create)
    event_id, event_title, event_description = create_demo_event(create_meet=create_meet)
    if not event_id:
        return

    # イベント取得 (Read)
    event = read_event(event_id)
    if not event:
        return

    # イベント更新 (Update)
    updated_event = update_event(event_id, event_title, event_description)
    if not updated_event:
        return

    # イベントリストの取得 (Read - list)
    list_events()

    # イベント削除 (Delete)
    delete_event_with_confirmation(event_id)

    print("\nデモ完了")


def test_create_meet_event():
    """Google Meetリンク付きのイベントを作成するテスト関数"""
    print("\n===== Google Meet作成テスト =====")
    calendar = initialize_calendar()
    if not calendar:
        print("カレンダーマネージャーの初期化に失敗しました")
        return

    print("\n【Google Meetリンク付きイベント作成】")
    event_title = "Meetテストイベント"
    event_description = "これはGoogle Meetリンク付きのテストイベントです"

    # 現在から2時間後に開始する1時間のイベント
    start_time = datetime.datetime.now() + datetime.timedelta(hours=2)
    end_time = start_time + datetime.timedelta(hours=1)

    new_event = calendar.create_event(
        summary=event_title,
        description=event_description,
        location="オンライン",
        start_time=start_time,
        end_time=end_time,
        create_meet=True,
    )

    if not new_event:
        print("イベント作成に失敗しました")
        return

    event_id = new_event.get("id")
    print(f"イベント作成成功: {new_event.get('summary')} (ID: {event_id})")
    print(f"開始時間: {calendar.format_event_time(new_event)}")

    # Google Meetのリンクがある場合は表示
    if "conferenceData" in new_event:
        print("\n【Google Meet情報】")
        print(f"Conference Data: {new_event.get('conferenceData')}")

        meet_link = (
            new_event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri", "リンクなし")
        )
        print(f"Google Meetリンク: {meet_link}")
    else:
        print("\n【Google Meet情報なし】")
        print(f"イベント全体: {new_event}")

    return event_id


if __name__ == "__main__":
    test_create_meet_event()
