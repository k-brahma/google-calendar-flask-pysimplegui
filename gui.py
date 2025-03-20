import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

import PySimpleGUI as sg
from gcal.calendar_manager import CalendarManager

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_events_df(calendar_manager):
    """カレンダーイベントをDataFrameとして取得"""
    JST = ZoneInfo("Asia/Tokyo")
    time_min = datetime.now(JST)
    time_max = time_min + timedelta(days=30)

    # UTC（Z）に変換
    time_min_utc = time_min.astimezone(ZoneInfo("UTC"))
    time_max_utc = time_max.astimezone(ZoneInfo("UTC"))

    events = calendar_manager.get_events(
        time_min=time_min_utc.isoformat().replace("+00:00", "Z"),
        time_max=time_max_utc.isoformat().replace("+00:00", "Z"),
        max_results=50,
    )

    # イベントデータをDataFrameに変換
    events_data = []
    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date", ""))
        if "T" in start_time:  # datetime形式の場合
            start_time = start_time.replace("T", " ").replace(":00+09:00", "")

        events_data.append(
            {
                "ID": event["id"],
                "タイトル": event["summary"],
                "開始時間": start_time,
                "場所": event.get("location", ""),
                "説明": (
                    event.get("description", "")[:50] + "..."
                    if event.get("description", "")
                    else ""
                ),
            }
        )

    return pd.DataFrame(events_data)


def create_window(df):
    """メインウィンドウを作成"""
    # テーマの設定
    sg.theme("LightBlue2")

    # DataFrameをテーブルデータに変換
    table_data = df.values.tolist()

    # 表示用のヘッダー（IDを除外）
    display_headers = [col for col in df.columns if col != "ID"]

    # 表示用のデータ（IDを除外）
    display_data = []
    for row in table_data:
        # IDは最初のカラムと仮定
        display_data.append(row[1:])

    # 編集用フレームの作成
    edit_frame = sg.Frame(
        "イベント詳細",
        [
            [sg.Text("タイトル"), sg.Input(key="-TITLE-", size=(40, 1))],
            [sg.Text("開始時間"), sg.Input(key="-START-", size=(20, 1))],
            [sg.Text("終了時間"), sg.Input(key="-END-", size=(20, 1))],
            [sg.Text("場所　　"), sg.Input(key="-LOCATION-", size=(40, 1))],
            [sg.Text("説明　　"), sg.Multiline(key="-DESCRIPTION-", size=(40, 5))],
            [
                sg.Button("保存"),
                sg.Button("削除", button_color=("white", "red")),
                sg.Button("キャンセル"),
                sg.Push(),
                sg.Button("新規作成", button_color=("white", "green")),
            ],
        ],
        key="-EDIT_FRAME-",
    )

    # レイアウトの作成
    layout = [
        [
            sg.Text("Google Calendar イベント一覧", font=("Any", 16)),
            sg.Push(),
            sg.Button("最新の状態を取得", key="更新"),
            sg.Button("終了"),
        ],
        [
            sg.Table(
                values=display_data,
                headings=display_headers,
                display_row_numbers=True,
                auto_size_columns=True,
                num_rows=10,
                enable_events=True,
                key="-TABLE-",
                justification="left",
                vertical_scroll_only=True,
            )
        ],
        [edit_frame],
    ]

    return sg.Window("Calendar GUI", layout, resizable=True, finalize=True)


def main():
    """メイン関数"""
    try:
        calendar_manager = CalendarManager()
        df = get_events_df(calendar_manager)
        window = create_window(df)
        current_event_id = None

        while True:
            event, values = window.read()

            if event in (sg.WIN_CLOSED, "終了"):
                break

            elif event == "更新":
                df = get_events_df(calendar_manager)
                window["-TABLE-"].update(values=df.values.tolist())
                # 更新時は編集フォームをクリア
                window["-TITLE-"].update("")
                window["-START-"].update("")
                window["-END-"].update("")
                window["-LOCATION-"].update("")
                window["-DESCRIPTION-"].update("")
                current_event_id = None

            elif event == "削除":
                if current_event_id:
                    # 削除確認ダイアログ
                    if sg.popup_yes_no("選択したイベントを削除しますか？", title="確認") == "Yes":
                        logger.info(f"イベント削除 - ID: {current_event_id}")
                        try:
                            # イベントを削除
                            if calendar_manager.delete_event(current_event_id):
                                sg.popup("イベントを削除しました")
                                # イベントリストを更新
                                df = get_events_df(calendar_manager)
                                window["-TABLE-"].update(values=df.values.tolist())
                            else:
                                sg.popup_error("イベントの削除に失敗しました")
                        except Exception as e:
                            logger.error(f"イベント削除エラー: {e}")
                            sg.popup_error(f"イベント削除中にエラーが発生しました:\n{e}")

                # 操作後はフォームをクリア
                window["-TITLE-"].update("")
                window["-START-"].update("")
                window["-END-"].update("")
                window["-LOCATION-"].update("")
                window["-DESCRIPTION-"].update("")
                current_event_id = None

            elif event == "キャンセル":
                # キャンセル時は編集フォームをクリア
                window["-TITLE-"].update("")
                window["-START-"].update("")
                window["-END-"].update("")
                window["-LOCATION-"].update("")
                window["-DESCRIPTION-"].update("")
                current_event_id = None

            elif event == "新規作成":
                # 新規作成用に編集フォームをクリア
                window["-TITLE-"].update("")
                window["-START-"].update("")
                window["-END-"].update("")
                window["-LOCATION-"].update("")
                window["-DESCRIPTION-"].update("")
                current_event_id = None

                # 現在時刻から1時間後の時間を設定（デフォルト）
                default_time = datetime.now() + timedelta(hours=1)
                window["-START-"].update(default_time.strftime("%Y-%m-%d %H:%M"))
                window["-END-"].update(
                    (default_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
                )

            elif event == "保存":
                # イベントの新規作成または更新
                try:
                    # フォームからデータを取得
                    title = values["-TITLE-"]
                    start_str = values["-START-"]
                    end_str = values["-END-"]
                    location = values["-LOCATION-"]
                    description = values["-DESCRIPTION-"]

                    # タイトルがない場合はエラー
                    if not title:
                        sg.popup_error("タイトルを入力してください")
                        continue

                    # 開始時間と終了時間を解析
                    try:
                        if not start_str:
                            sg.popup_error("開始時間を入力してください")
                            continue
                        start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M")

                        if end_str:
                            end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
                            # 終了時間が開始時間より前の場合はエラー
                            if end_time <= start_time:
                                sg.popup_error("終了時間は開始時間より後にしてください")
                                continue
                        else:
                            # 終了時間が未入力の場合は開始時間の1時間後を設定
                            end_time = start_time + timedelta(hours=1)
                    except ValueError:
                        # 日付解析エラー
                        sg.popup_error("時間の形式が正しくありません。\n例: 2025-01-01 09:00")
                        continue

                    if current_event_id:
                        # 既存イベントの更新
                        logger.info(f"イベント更新 - ID: {current_event_id}")
                        updated_event = calendar_manager.update_event(
                            event_id=current_event_id,
                            summary=title,
                            start_time=start_time,
                            end_time=end_time,
                            description=description,
                            location=location,
                        )

                        if updated_event:
                            sg.popup("イベントを更新しました")
                        else:
                            sg.popup_error("イベントの更新に失敗しました")
                    else:
                        # 新規イベントの作成
                        logger.info(f"イベント新規作成 - タイトル: {title}")
                        created_event = calendar_manager.create_event(
                            summary=title,
                            start_time=start_time,
                            end_time=end_time,
                            description=description,
                            location=location,
                        )

                        if created_event:
                            sg.popup("イベントを作成しました")
                        else:
                            sg.popup_error("イベントの作成に失敗しました")

                    # イベントリストを更新
                    df = get_events_df(calendar_manager)
                    window["-TABLE-"].update(values=df.values.tolist())
                except Exception as e:
                    logger.error(f"イベント保存エラー: {e}")
                    sg.popup_error(f"イベント保存中にエラーが発生しました:\n{e}")

                # 保存後は編集フォームをクリア
                window["-TITLE-"].update("")
                window["-START-"].update("")
                window["-END-"].update("")
                window["-LOCATION-"].update("")
                window["-DESCRIPTION-"].update("")
                current_event_id = None

            elif event == "-TABLE-":
                if values["-TABLE-"]:  # 行が選択されている場合
                    selected_row = values["-TABLE-"][0]
                    event_id = df.iloc[selected_row]["ID"]
                    event_title = df.iloc[selected_row]["タイトル"]
                    event_start = df.iloc[selected_row]["開始時間"]
                    event_location = df.iloc[selected_row]["場所"]
                    event_description = df.iloc[selected_row]["説明"]

                    # 選択されたイベントの詳細情報を取得
                    selected_event = calendar_manager.get_event(event_id)
                    end_time = ""
                    if selected_event and "end" in selected_event:
                        end_time = selected_event["end"].get(
                            "dateTime", selected_event["end"].get("date", "")
                        )
                        if "T" in end_time:  # datetime形式の場合
                            end_time = end_time.replace("T", " ").replace(":00+09:00", "")

                    # フォームに値を設定
                    window["-TITLE-"].update(event_title)
                    window["-START-"].update(event_start)
                    window["-END-"].update(end_time)
                    window["-LOCATION-"].update(event_location)
                    window["-DESCRIPTION-"].update(event_description)
                    window["-EDIT_FRAME-"].update(visible=True)

                    current_event_id = event_id
                    logger.info(f"選択されたイベント - ID: {event_id}, タイトル: {event_title}")

        window.close()

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sg.popup_error(f"エラーが発生しました:\n{e}")


if __name__ == "__main__":
    main()
