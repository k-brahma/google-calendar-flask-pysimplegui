import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup

from gcal.calendar_manager import CalendarManager


# PyInstallerでのリソースパス取得のためのヘルパー関数
def resource_path(relative_path):
    """リソースの絶対パスを取得する関数"""
    try:
        # PyInstallerでバンドルされている場合のパス
        base_path = sys._MEIPASS
    except Exception:
        # 通常実行の場合のパス
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# .envファイルから環境変数を読み込む
dotenv_path = resource_path(".env")  # リソースパス関数を使用
load_dotenv(dotenv_path)

# デバッグモードの設定
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

app = Flask(__name__)

# 環境変数からSECRET_KEYを取得し、ない場合はエラーを発生させる
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError(
        "環境変数SECRET_KEYが設定されていません。セキュリティのため、アプリケーションを起動できません。"
    )

app.secret_key = secret_key

# CSRF保護を有効化
csrf = CSRFProtect(app)

# タイムゾーンの設定
JST = ZoneInfo("Asia/Tokyo")


# nl2brフィルターを追加
@app.template_filter("nl2br")
def nl2br_filter(text):
    if not text:
        return text
    return Markup(str(text).replace("\n", "<br>"))


# CalendarManagerのインスタンスを作成
calendar_manager = None
try:
    calendar_manager = CalendarManager()
except Exception as e:
    print(f"カレンダーマネージャーの初期化エラー: {e}")


@app.route("/")
def index():
    """イベント一覧ページ"""
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
        print("calendar_managerが初期化されていません")
    return render_template("index.html", events=events)


@app.route("/event/<event_id>")
def event_detail(event_id):
    """イベント詳細ページ"""
    if not calendar_manager:
        flash("カレンダーマネージャーが初期化されていません", "error")
        return redirect(url_for("index"))

    event = calendar_manager.get_event(event_id)
    if not event:
        flash("イベントが見つかりませんでした", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", event=event)


@app.route("/event/create", methods=["GET", "POST"])
def event_create():
    """イベント作成ページ"""
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
def event_update(event_id):
    """イベント更新ページ"""
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
def event_delete(event_id):
    """イベント削除ページ"""
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
