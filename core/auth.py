"""Authentication and credential setup helpers."""

import os
import tempfile
from functools import wraps

from flask import flash, redirect, session, url_for

from core.runtime import is_pyinstaller_environment, resource_path
from crypto_utils import decrypt_file
from gcal.calendar_manager import CalendarManager


def setup_credentials(session_obj):
    """Decrypt bundled credentials into a temporary directory.

    :param session_obj: Flask session object.
    :return: Tuple of temporary directory path and error message.
    :rtype: tuple[str | None, str | None]
    """
    if "credentials_password" not in session_obj:
        return None, "認証情報のパスワードが設定されていません。"

    password = session_obj["credentials_password"]

    try:
        encrypted_dir = resource_path("encrypted_credentials")
        encrypted_files = []

        for root, _dirs, files in os.walk(encrypted_dir):
            for file_name in files:
                if file_name.endswith(".encrypted"):
                    encrypted_files.append(os.path.join(root, file_name))

        if not encrypted_files:
            return None, "暗号化された認証情報ファイルが見つかりません。"

        temp_dir = tempfile.mkdtemp(prefix="app_credentials_")

        for encrypted_file in encrypted_files:
            relative_path = os.path.relpath(encrypted_file, encrypted_dir)
            if relative_path.endswith(".encrypted"):
                relative_path = relative_path[:-10]

            output_path = os.path.join(temp_dir, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            decrypt_file(encrypted_file, password, output_path)

        return temp_dir, None
    except Exception as exc:
        return None, f"認証情報の復号化エラー: {str(exc)}"


def requires_auth(view_func):
    """Protect routes that require decrypted credentials.

    :param view_func: Flask view function.
    :return: Wrapped view function.
    """

    @wraps(view_func)
    def decorated(*args, **kwargs):
        if is_pyinstaller_environment() and "credentials_password" not in session:
            flash("認証が必要です", "error")
            return redirect(url_for("authenticate"))
        return view_func(*args, **kwargs)

    return decorated


def get_calendar_manager(session_obj):
    """Create a :class:`CalendarManager` for the current runtime.

    :param session_obj: Flask session object.
    :return: Calendar manager instance or ``None``.
    :rtype: CalendarManager | None
    """
    if is_pyinstaller_environment():
        print("PyInstallerでビルドされた環境で実行中")
        if not session_obj.get("credentials_password"):
            return None

        try:
            creds_dir, error = setup_credentials(session_obj)
            if error or not creds_dir:
                print(f"認証情報エラー: {error}")
                return None

            config_file = os.path.join(creds_dir, "config.json")
            return CalendarManager(config_file=config_file, key_dir=creds_dir)
        except Exception as exc:
            print(f"カレンダーマネージャーの初期化エラー: {exc}")
            return None

    print("通常のPython環境で実行中")
    try:
        return CalendarManager()
    except Exception as exc:
        print(f"カレンダーマネージャーの初期化エラー: {exc}")
        return None
