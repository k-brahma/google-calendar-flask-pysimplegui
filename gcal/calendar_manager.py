import datetime
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


class CalendarManager:
    """Google Calendarの操作を行うマネージャークラス"""

    def __init__(self, config_file="credentials/config.json", key_dir="credentials"):
        """
        CalendarManagerの初期化

        Args:
            config_file: 設定ファイルのパス
            key_dir: 認証キーファイルの存在するディレクトリ
        """
        # パスの調整
        base_dir = self._get_base_dir()
        self.config_file = os.path.join(base_dir, config_file)
        self.key_dir = os.path.join(base_dir, key_dir)
        self.config = self._load_config()
        self.service = self._create_service()

    def _get_base_dir(self):
        """ベースディレクトリ（プロジェクトルート）を取得"""
        # 現在のファイルパス
        current_file = Path(__file__).resolve()
        # calendarディレクトリの親 = プロジェクトルート
        return str(current_file.parent.parent)

    def _load_config(self):
        """設定ファイルを読み込む"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")

        with open(self.config_file, "r") as f:
            return json.load(f)

    def _find_key_file(self):
        """サービスアカウントキーのファイルパスを探す"""
        for file in os.listdir(self.key_dir):
            if file.endswith(".json") and file not in ["credentials.json", "config.json"]:
                return os.path.join(self.key_dir, file)
        return None

    def _create_service(self):
        """Google Calendar APIサービスを作成"""
        key_file = self._find_key_file()
        if not key_file:
            raise FileNotFoundError("サービスアカウントキーファイルが見つかりません")

        try:
            # スコープの設定
            scopes = ["https://www.googleapis.com/auth/calendar"]

            # サービスアカウントの認証情報を作成
            credentials = service_account.Credentials.from_service_account_file(
                key_file, scopes=scopes
            )

            # なりすましが設定されている場合は適用
            if "impersonation_email" in self.config.get("auth_settings", {}):
                impersonation_email = self.config["auth_settings"]["impersonation_email"]
                if impersonation_email:
                    credentials = credentials.with_subject(impersonation_email)
                    print(f"サービスアカウントが {impersonation_email} としてAPIにアクセスします")

            # サービスの作成
            service = build("calendar", "v3", credentials=credentials)
            print(f"サービスアカウントキーを使用して接続しました: {os.path.basename(key_file)}")
            return service
        except Exception as e:
            raise ConnectionError(f"サービス接続エラー: {str(e)}")

    @property
    def timezone(self):
        """タイムゾーンを取得"""
        return self.config["calendar_settings"]["timezone"]

    @property
    def default_calendar_id(self):
        """デフォルトカレンダーIDを取得"""
        return self.config["calendar_settings"].get("default_calendar_id", "primary")

    @property
    def target_calendar_id(self):
        """ターゲットカレンダーIDを取得"""
        return self.config["calendar_settings"].get("target_calendar_id", self.default_calendar_id)

    def get_calendar_list(self):
        """利用可能なカレンダーリストを取得"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get("items", [])
        except Exception as e:
            print(f"カレンダーリスト取得エラー: {str(e)}")
            # エラーの詳細情報を追加
            import traceback

            print(f"エラー詳細: {traceback.format_exc()}")
            return []

    def get_events(
        self,
        calendar_id=None,
        max_results=10,
        time_min=None,
        time_max=None,
        search_text=None,
        order_by="startTime",
    ):
        """イベントを取得

        Args:
            calendar_id: カレンダーID（省略時はターゲットカレンダー）
            max_results: 取得する最大イベント数
            time_min: この時間以降のイベントを取得（省略時は現在時刻）
            time_max: この時間以前のイベントを取得（省略時は制限なし）
            search_text: 検索テキスト
            order_by: 並び順（startTime, updated）

        Returns:
            イベントのリスト
        """
        if calendar_id is None:
            calendar_id = self.target_calendar_id

        if time_min is None:
            time_min = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z'はUTC

        try:
            params = {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": order_by,
            }

            if time_max:
                params["timeMax"] = time_max

            if search_text:
                params["q"] = search_text

            events_result = self.service.events().list(**params).execute()
            return events_result.get("items", [])
        except Exception as e:
            print(f"イベント取得エラー: {str(e)}")
            return []

    def get_event(self, event_id, calendar_id=None):
        """特定のイベントを取得

        Args:
            event_id: イベントID
            calendar_id: カレンダーID（省略時はターゲットカレンダー）

        Returns:
            イベント情報、取得失敗時はNone
        """
        if calendar_id is None:
            calendar_id = self.target_calendar_id

        try:
            return self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except Exception as e:
            print(f"イベント取得エラー: {str(e)}")
            return None

    def create_event(
        self,
        summary,
        start_time=None,
        end_time=None,
        description="",
        location="",
        calendar_id=None,
        attendees=None,
        reminders=None,
        create_meet=False,  # 現在は機能していません
    ):
        """イベントを作成

        Args:
            summary: イベントタイトル
            start_time: 開始時間（datetimeオブジェクト、省略時は1時間後）
            end_time: 終了時間（datetimeオブジェクト、省略時は開始時間の1時間後）
            description: 説明
            location: 場所
            calendar_id: カレンダーID（省略時はターゲットカレンダー）
            attendees: 参加者のメールアドレスのリスト
            reminders: リマインダー設定（辞書形式）
            create_meet: Google Meetリンク作成（現在は機能していません）

        Returns:
            作成されたイベント情報、作成失敗時はNone
        """
        if calendar_id is None:
            calendar_id = self.target_calendar_id

        # 開始・終了時間のデフォルト値設定
        if start_time is None:
            start_time = datetime.datetime.now() + datetime.timedelta(hours=1)

        if end_time is None:
            end_time = start_time + datetime.timedelta(hours=1)

        # イベントデータの作成
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": self.timezone,
            },
        }

        # Google Meetの作成機能はWorkspace有料版のみ対応のため無効化
        if create_meet:
            print("Google Meetリンクの作成には有料版が必要です")

        # 参加者がいる場合は追加
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        # リマインダー設定がある場合は追加
        if reminders:
            event["reminders"] = reminders

        try:
            kwargs = {"calendarId": calendar_id, "body": event}

            return self.service.events().insert(**kwargs).execute()
        except Exception as e:
            print(f"イベント作成エラー: {str(e)}")
            # デバッグ情報を追加
            import traceback

            print(f"エラー詳細: {traceback.format_exc()}")
            return None

    def update_event(
        self,
        event_id,
        summary=None,
        start_time=None,
        end_time=None,
        description=None,
        location=None,
        calendar_id=None,
        attendees=None,
    ):
        """イベントを更新

        Args:
            event_id: 更新するイベントID
            summary: 更新後のタイトル（省略時は変更なし）
            start_time: 更新後の開始時間（省略時は変更なし）
            end_time: 更新後の終了時間（省略時は変更なし）
            description: 更新後の説明（省略時は変更なし）
            location: 更新後の場所（省略時は変更なし）
            calendar_id: カレンダーID（省略時はターゲットカレンダー）
            attendees: 更新後の参加者リスト（省略時は変更なし）

        Returns:
            更新されたイベント情報、更新失敗時はNone
        """
        if calendar_id is None:
            calendar_id = self.target_calendar_id

        # 現在のイベント情報を取得
        event = self.get_event(event_id, calendar_id)
        if not event:
            print(f"更新対象のイベントが見つかりません: {event_id}")
            return None

        # 更新するフィールドを設定
        if summary:
            event["summary"] = summary

        if description is not None:  # 空文字列も許容
            event["description"] = description

        if location is not None:  # 空文字列も許容
            event["location"] = location

        if start_time:
            event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": self.timezone,
            }

        if end_time:
            event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": self.timezone,
            }

        if attendees is not None:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            return (
                self.service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event)
                .execute()
            )
        except Exception as e:
            print(f"イベント更新エラー: {str(e)}")
            return None

    def delete_event(self, event_id, calendar_id=None):
        """イベントを削除

        Args:
            event_id: 削除するイベントID
            calendar_id: カレンダーID（省略時はターゲットカレンダー）

        Returns:
            削除成功時はTrue、失敗時はFalse
        """
        if calendar_id is None:
            calendar_id = self.target_calendar_id

        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"イベント削除エラー: {str(e)}")
            return False

    def format_event_time(self, event):
        """イベントの時間を見やすくフォーマット

        Args:
            event: イベント情報

        Returns:
            フォーマットされた日時文字列
        """
        start = event["start"].get("dateTime", event["start"].get("date"))

        if "T" in start:  # dateTime形式
            dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        else:  # date形式
            return start
