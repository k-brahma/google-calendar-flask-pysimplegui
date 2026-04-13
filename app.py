import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup

from core.auth import get_calendar_manager, get_spreadsheet_manager, requires_auth, setup_credentials
from core.constants import JST
from core.multi_demo_service import build_multi_demo_rows, create_multi_demo_events, flush_future_events
from core.spreadsheet_demo_service import build_spreadsheet_demo_rows, create_spreadsheet_demo_events
from core.runtime import resource_path


# .envファイルから環境変数を読み込む
dotenv_path = resource_path(".env")  # リソースパス関数を使用
load_dotenv(dotenv_path)

# デバッグモードの設定
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

app = Flask(__name__)

# 環境変数からSECRET_KEYを取得し、ない場合はエラーを発生させる
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    secret_key = "default-secret-key-for-development-only"
    print("警告: 環境変数SECRET_KEYが設定されていません。デフォルト値を使用します。")

app.secret_key = secret_key

# CSRF保護を有効化
csrf = CSRFProtect(app)



# nl2brフィルターを追加
@app.template_filter("nl2br")
def nl2br_filter(text):
    if not text:
        return text
    return Markup(str(text).replace("\n", "<br>"))


# 認証ルート
@app.route("/auth", methods=["GET", "POST"])
def authenticate():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password:
            session["credentials_password"] = password
            # 認証情報をセットアップ
            creds_dir, error = setup_credentials(session)
            if error:
                flash(f"認証エラー: {error}", "error")
                session.pop("credentials_password", None)
                return render_template("auth.html")
            flash("認証に成功しました", "success")
            return redirect(url_for("index"))
        else:
            flash("パスワードを入力してください", "error")

    return render_template("auth.html")


@app.route("/")
@requires_auth
def index():
    """イベント一覧ページ"""
    calendar_manager = get_calendar_manager(session)
    events = []

    if calendar_manager:
        # 今日から30日分のイベントを取得
        time_min = datetime.now(JST)
        time_max = time_min + timedelta(days=30)

        # UTC（Z）に変換
        time_min_utc = time_min.astimezone(ZoneInfo("UTC"))
        time_max_utc = time_max.astimezone(ZoneInfo("UTC"))

        print(f"時間範囲: {time_min_utc.isoformat()} から {time_max_utc.isoformat()}")

        try:
            events = calendar_manager.get_events(
                time_min=time_min_utc.isoformat().replace("+00:00", "Z"),
                time_max=time_max_utc.isoformat().replace("+00:00", "Z"),
                max_results=50,
            )
            print(f"取得したイベント数: {len(events)}")
            if events:
                print(f"最初のイベント: {events[0]}")
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            events = []
    else:
        print("calendar_managerの初期化に失敗しました")

    return render_template("index.html", events=events)


@app.route("/event/<event_id>")
@requires_auth
def event_detail(event_id):
    """イベント詳細ページ"""
    calendar_manager = get_calendar_manager(session)
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    event = calendar_manager.get_event(event_id)
    if not event:
        flash("イベントが見つかりませんでした", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", event=event)


@app.route("/event/create", methods=["GET", "POST"])
@requires_auth
def event_create():
    """イベント作成ページ"""
    calendar_manager = get_calendar_manager(session)
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # フォームからデータを取得
        summary = request.form.get("summary", "")
        description = request.form.get("description", "")
        location = request.form.get("location", "")

        # 日時の処理
        start_date = request.form.get("start_date", "")
        start_time = request.form.get("start_time", "")
        end_date = request.form.get("end_date", "")
        end_time = request.form.get("end_time", "")

        try:
            # 開始時間の作成
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")

            # 終了時間の作成（入力がない場合は開始時間の1時間後）
            if end_date and end_time:
                end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            else:
                end_datetime = start_datetime + timedelta(hours=1)

            # イベント作成
            new_event = calendar_manager.create_event(
                summary=summary,
                description=description,
                location=location,
                start_time=start_datetime,
                end_time=end_datetime,
            )

            if new_event:
                flash("イベントが作成されました", "success")
                return redirect(url_for("event_detail", event_id=new_event.get("id")))
            else:
                flash("イベントの作成に失敗しました", "error")
        except Exception as e:
            flash(f"エラーが発生しました: {str(e)}", "error")

    # GETリクエストまたはエラー時
    # デフォルト値として現在時刻+1時間を設定
    default_start = datetime.now() + timedelta(hours=1)
    default_end = default_start + timedelta(hours=1)

    return render_template(
        "create.html",
        default_start_date=default_start.strftime("%Y-%m-%d"),
        default_start_time=default_start.strftime("%H:%M"),
        default_end_date=default_end.strftime("%Y-%m-%d"),
        default_end_time=default_end.strftime("%H:%M"),
    )


@app.route("/event/update/<event_id>", methods=["GET", "POST"])
@requires_auth
def event_update(event_id):
    """イベント更新ページ"""
    calendar_manager = get_calendar_manager(session)
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    # 現在のイベント情報を取得
    event = calendar_manager.get_event(event_id)
    if not event:
        flash("イベントが見つかりませんでした", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # フォームからデータを取得
        summary = request.form.get("summary", "")
        description = request.form.get("description", "")
        location = request.form.get("location", "")

        # 日時の処理
        start_date = request.form.get("start_date", "")
        start_time = request.form.get("start_time", "")
        end_date = request.form.get("end_date", "")
        end_time = request.form.get("end_time", "")

        try:
            # 開始時間の作成
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")

            # 終了時間の作成
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

            # イベント更新
            updated_event = calendar_manager.update_event(
                event_id=event_id,
                summary=summary,
                description=description,
                location=location,
                start_time=start_datetime,
                end_time=end_datetime,
            )

            if updated_event:
                flash("イベントが更新されました", "success")
                return redirect(url_for("event_detail", event_id=event_id))
            else:
                flash("イベントの更新に失敗しました", "error")
        except Exception as e:
            flash(f"エラーが発生しました: {str(e)}", "error")

    # イベントの日時情報を取得
    start = event.get("start", {})
    end = event.get("end", {})

    # 日時をパースする（ISO 8601形式）
    start_datetime = None
    end_datetime = None

    if "dateTime" in start:
        start_datetime = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))

    if "dateTime" in end:
        end_datetime = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))

    return render_template(
        "update.html",
        event=event,
        event_id=event_id,
        start_date=start_datetime.strftime("%Y-%m-%d") if start_datetime else "",
        start_time=start_datetime.strftime("%H:%M") if start_datetime else "",
        end_date=end_datetime.strftime("%Y-%m-%d") if end_datetime else "",
        end_time=end_datetime.strftime("%H:%M") if end_datetime else "",
    )


@app.route("/event/delete/<event_id>", methods=["GET", "POST"])
@requires_auth
def event_delete(event_id):
    """イベント削除ページ"""
    calendar_manager = get_calendar_manager(session)
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    # 現在のイベント情報を取得
    event = calendar_manager.get_event(event_id)
    if not event:
        flash("イベントが見つかりませんでした", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # イベント削除
        if calendar_manager.delete_event(event_id):
            flash("イベントが削除されました", "success")
            return redirect(url_for("index"))
        else:
            flash("イベントの削除に失敗しました", "error")

    return render_template("delete.html", event=event, event_id=event_id)


@app.route("/multi", methods=["GET", "POST"])
@requires_auth
def multi_demo():
    """CSV / XLSX デモ用の一括予定作成ページ。"""
    calendar_manager = get_calendar_manager(session)
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action", "refresh")

        try:
            if action == "create":
                created_count, skipped_count, failed_summaries = create_multi_demo_events(calendar_manager, session)
                if created_count:
                    flash(f"{created_count}件のデモ予定を作成しました", "success")
                if skipped_count:
                    flash(f"{skipped_count}件は既に存在していたため再作成していません", "info")
                if failed_summaries:
                    flash(f"作成に失敗した予定: {', '.join(failed_summaries)}", "error")
            elif action == "flush":
                deleted_count, failed_count = flush_future_events(calendar_manager, session)
                flash(f"先日付イベントを{deleted_count}件削除しました", "warning")
                if failed_count:
                    flash(f"{failed_count}件の削除に失敗しました", "error")
            else:
                flash("Google カレンダーの最新状態を再取得しました", "success")
        except FileNotFoundError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception as exc:
            flash(f"/multi データの処理に失敗しました: {exc}", "error")

        return redirect(url_for("multi_demo"))

    try:
        rows = build_multi_demo_rows(calendar_manager, session)
    except FileNotFoundError as exc:
        flash(str(exc), "error")
        rows = []
    except ValueError as exc:
        flash(str(exc), "error")
        rows = []
    except Exception as exc:
        flash(f"/multi データの読み込みに失敗しました: {exc}", "error")
        rows = []

    created_count = sum(1 for row in rows if row["exists"])
    assignees = sorted({row["assignee"] for row in rows})
    day_span = max((row["day_offset"] for row in rows), default=0)
    synced_at_label = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        "multi.html",
        rows=rows,
        created_count=created_count,
        assignees=assignees,
        day_span=day_span,
        synced_at_label=synced_at_label,
    )


@app.route("/spreadsheet", methods=["GET", "POST"])
@requires_auth
def spreadsheet_demo():
    """Google Spreadsheet から取り込んだ予定を表示するページ。"""
    spreadsheet_manager = get_spreadsheet_manager(session)
    if not spreadsheet_manager:
        flash("スプレッドシートマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action", "refresh")

        if action in {"create", "flush"}:
            calendar_manager = get_calendar_manager(session)
            if not calendar_manager:
                flash("カレンダーマネージャーが初期化されていません", "error")
                return redirect(url_for("index"))

            if action == "create":
                try:
                    created_count, skipped_count, failed_summaries = create_spreadsheet_demo_events(
                        calendar_manager,
                        session,
                        spreadsheet_manager,
                    )
                    if created_count:
                        flash(f"{created_count}件の予定をGoogle カレンダーへ作成しました", "success")
                    if skipped_count:
                        flash(f"{skipped_count}件は既に存在していたため再作成していません", "info")
                    if failed_summaries:
                        flash(f"作成に失敗した予定: {', '.join(failed_summaries)}", "error")
                except Exception as exc:
                    flash(f"Google カレンダーへの流し込みに失敗しました: {exc}", "error")
            else:
                deleted_count, failed_count = flush_future_events(calendar_manager, session)
                flash(f"先日付イベントを{deleted_count}件削除しました", "warning")
                if failed_count:
                    flash(f"{failed_count}件の削除に失敗しました", "error")
        else:
            flash("Google Spreadsheet の最新状態を再取得しました", "success")

        return redirect(url_for("spreadsheet_demo"))

    rows = []
    spreadsheet_title = "-"
    range_name = "-"

    try:
        rows = build_spreadsheet_demo_rows(spreadsheet_manager)
        spreadsheet_title = spreadsheet_manager.get_sheet_title() or spreadsheet_manager.spreadsheet_id
        range_name = spreadsheet_manager.range_name
    except Exception as exc:
        flash(f"Google Spreadsheetの読み込みに失敗しました: {exc}", "error")

    synced_at_label = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        "spreadsheet.html",
        rows=rows,
        imported_count=len(rows),
        spreadsheet_title=spreadsheet_title,
        range_name=range_name,
        synced_at_label=synced_at_label,
    )


# アプリケーション起動時の環境情報をログに出力
print(f"Working directory: {os.getcwd()}")
try:
    base_path = sys._MEIPASS
    print(f"Running in PyInstaller bundle. Base path: {base_path}")
    print(f"Contents of base path: {os.listdir(base_path)}")
except Exception:
    print("Running in normal Python environment")


if __name__ == "__main__":
    app.run(debug=DEBUG)
