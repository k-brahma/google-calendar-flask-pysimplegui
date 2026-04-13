"""Google Spreadsheet access helper."""

import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


class SpreadsheetManager:
    """Google Spreadsheet の読み取りを行うマネージャークラス"""

    def __init__(self, config_file="credentials/config.json", key_dir="credentials"):
        base_dir = self._get_base_dir()
        self.config_file = os.path.join(base_dir, config_file)
        self.key_dir = os.path.join(base_dir, key_dir)
        self.config = self._load_config()
        self.service = self._create_service()

    def _get_base_dir(self):
        """ベースディレクトリ（プロジェクトルート）を取得"""
        current_file = Path(__file__).resolve()
        return str(current_file.parent.parent)

    def _load_config(self):
        """設定ファイルを読み込む"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")

        with open(self.config_file, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)

    def _find_key_file(self):
        """サービスアカウントキーのファイルパスを探す"""
        for file_name in os.listdir(self.key_dir):
            if file_name.endswith(".json") and file_name not in ["credentials.json", "config.json"]:
                return os.path.join(self.key_dir, file_name)
        return None

    def _create_service(self):
        """Google Sheets APIサービスを作成"""
        key_file = self._find_key_file()
        if not key_file:
            raise FileNotFoundError("サービスアカウントキーファイルが見つかりません")

        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            credentials = service_account.Credentials.from_service_account_file(
                key_file, scopes=scopes
            )

            impersonation_email = self.config.get("auth_settings", {}).get("impersonation_email")
            if impersonation_email:
                credentials = credentials.with_subject(impersonation_email)
                print(f"サービスアカウントが {impersonation_email} としてSheets APIにアクセスします")

            service = build("sheets", "v4", credentials=credentials)
            print(f"Google Spreadsheetに接続しました: {os.path.basename(key_file)}")
            return service
        except Exception as exc:
            raise ConnectionError(f"Google Spreadsheet接続エラー: {str(exc)}") from exc

    @property
    def spreadsheet_id(self):
        """対象スプレッドシートIDを取得"""
        spreadsheet_id = self.config.get("spreadsheet_settings", {}).get("spreadsheet_id")
        if not spreadsheet_id:
            raise KeyError("config.json の spreadsheet_settings.spreadsheet_id が設定されていません")
        return spreadsheet_id

    @property
    def range_name(self):
        """取得対象のA1表記範囲を取得"""
        configured_range = self.config.get("spreadsheet_settings", {}).get("range_name")
        if configured_range:
            return configured_range
        return f"{self.get_first_sheet_title()}!A:Z"

    def get_first_sheet_title(self):
        """先頭シートのタイトルを取得"""
        metadata = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            fields="sheets.properties.title",
        ).execute()
        sheets = metadata.get("sheets", [])
        if not sheets:
            raise ValueError("スプレッドシート内に参照可能なシートが見つかりません")
        return sheets[0].get("properties", {}).get("title", "Sheet1")

    def get_sheet_title(self):
        """対象スプレッドシートのタイトルを取得"""
        metadata = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            fields="properties.title",
        ).execute()
        return metadata.get("properties", {}).get("title")

    def get_values(self, spreadsheet_id=None, range_name=None):
        """対象範囲の値を取得"""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id or self.spreadsheet_id,
            range=range_name or self.range_name,
        ).execute()
        return result.get("values", [])

    def get_records(self, spreadsheet_id=None, range_name=None):
        """ヘッダー行を使ってレコード一覧を取得"""
        values = self.get_values(spreadsheet_id=spreadsheet_id, range_name=range_name)
        if not values:
            return []

        headers = [str(header).strip() for header in values[0]]
        records = []
        for row in values[1:]:
            padded_row = list(row) + [""] * (len(headers) - len(row))
            record = {
                header: str(padded_row[index]).strip()
                for index, header in enumerate(headers)
                if header
            }
            if any(record.values()):
                records.append(record)

        return records
