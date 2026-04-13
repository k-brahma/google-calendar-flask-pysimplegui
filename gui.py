import logging
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from core.multi_demo_service import flush_future_events
from core.spreadsheet_demo_service import (
    build_spreadsheet_sync_rows,
    create_spreadsheet_demo_events,
)
from gcal.calendar_manager import CalendarManager
from gsheets.spreadsheet_manager import SpreadsheetManager


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LocalSessionState(dict):
    """Minimal session-like store used by shared demo services."""

    def __init__(self):
        super().__init__()
        self.modified = False


class SpreadsheetCalendarGUI:
    def __init__(self, root):
        """Google Spreadsheet と Google Calendar 連携デモの初期化"""
        self.root = root
        self.root.title("Google Spreadsheet -> Google Calendar デモ")
        self.root.geometry("1320x820")
        self.root.minsize(1080, 700)

        self.session_state = LocalSessionState()
        self.rows = []
        self.item_row_map = {}

        try:
            self.calendar_manager = CalendarManager()
            self.spreadsheet_manager = SpreadsheetManager()
        except Exception as exc:
            logger.error("マネージャー初期化エラー: %s", exc)
            messagebox.showerror("エラー", f"初期化に失敗しました:\n{exc}")
            self.root.after(0, self.root.destroy)
            return

        self.subtitle_var = tk.StringVar(value="スプレッドシート接続中...")
        self.status_var = tk.StringVar(value="読み込み待機中")
        self.detail_var = tk.StringVar(value="行を選択すると詳細を表示します。")

        self.create_widgets()
        self.refresh_rows(show_message=False)

    def create_widgets(self):
        """ウィジェットを作成する"""
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(
            title_frame,
            text="Google Spreadsheet 連携デモ",
            font=("Meiryo UI", 18, "bold"),
        ).pack(anchor=tk.W)
        ttk.Label(title_frame, textvariable=self.subtitle_var).pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(title_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(2, 0))

        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(button_frame, text="Google Spreadsheet を再取得", command=self.refresh_rows).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(button_frame, text="カレンダーに流し込み", command=self.create_events).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(button_frame, text="先日付予定をFLUSH", command=self.flush_events).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(button_frame, text="終了", command=self.root.quit).pack(side=tk.LEFT)

        table_frame = ttk.LabelFrame(main_frame, text="Google Spreadsheet の予定一覧")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        columns = ("date", "assignee", "summary", "planned_time", "status", "actual_summary")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("date", text="日付")
        self.tree.heading("assignee", text="担当")
        self.tree.heading("summary", text="予定案")
        self.tree.heading("planned_time", text="予定時間")
        self.tree.heading("status", text="同期状況")
        self.tree.heading("actual_summary", text="カレンダー上の予定")
        self.tree.column("date", width=110, minwidth=100, anchor=tk.W)
        self.tree.column("assignee", width=120, minwidth=110, anchor=tk.W)
        self.tree.column("summary", width=280, minwidth=220, anchor=tk.W)
        self.tree.column("planned_time", width=180, minwidth=160, anchor=tk.W)
        self.tree.column("status", width=140, minwidth=120, anchor=tk.W)
        self.tree.column("actual_summary", width=320, minwidth=220, anchor=tk.W)

        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        detail_outer = ttk.LabelFrame(main_frame, text="選択中の詳細")
        detail_outer.pack(fill=tk.BOTH, expand=False)
        detail_outer.columnconfigure(0, weight=1)
        detail_outer.columnconfigure(1, weight=1)

        ttk.Label(detail_outer, textvariable=self.detail_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=8, pady=(8, 4)
        )

        plan_frame = ttk.LabelFrame(detail_outer, text="Spreadsheet の予定案")
        plan_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        actual_frame = ttk.LabelFrame(detail_outer, text="Google Calendar 上の状態")
        actual_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))
        detail_outer.rowconfigure(1, weight=1)

        self.plan_text = tk.Text(plan_frame, height=14, wrap=tk.WORD)
        self.plan_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.actual_text = tk.Text(actual_frame, height=14, wrap=tk.WORD)
        self.actual_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._set_text(self.plan_text, "")
        self._set_text(self.actual_text, "")

    def _set_text(self, widget, content):
        """Set read-only text content."""
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.config(state=tk.DISABLED)

    def refresh_rows(self, show_message=True):
        """Google Spreadsheet とカレンダー状態を再取得する"""
        try:
            self.rows = build_spreadsheet_sync_rows(
                self.calendar_manager,
                self.session_state,
                self.spreadsheet_manager,
            )
            spreadsheet_title = self.spreadsheet_manager.get_sheet_title() or self.spreadsheet_manager.spreadsheet_id
            self.subtitle_var.set(
                f"接続先: {spreadsheet_title} / 範囲: {self.spreadsheet_manager.range_name}"
            )
            self.status_var.set(
                f"取り込み件数: {len(self.rows)} / 最終取得: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.update_table()
            self.clear_detail()
            if show_message:
                messagebox.showinfo("完了", "Google Spreadsheet の最新状態を再取得しました")
        except Exception as exc:
            logger.error("Spreadsheet再取得エラー: %s", exc)
            messagebox.showerror("エラー", f"Google Spreadsheet の読み込みに失敗しました:\n{exc}")

    def update_table(self):
        """一覧テーブルを更新する"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_row_map = {}
        for row in self.rows:
            values = (
                row["target_date"].strftime("%Y-%m-%d"),
                row["assignee"],
                row["summary"],
                row["planned_time_label"],
                row["status_label"],
                row["actual_summary"] if row["exists"] else "-",
            )
            item_id = self.tree.insert("", tk.END, values=values)
            self.item_row_map[item_id] = row

    def clear_detail(self):
        """詳細表示をクリアする"""
        self.detail_var.set("行を選択すると詳細を表示します。")
        self._set_text(self.plan_text, "")
        self._set_text(self.actual_text, "")

    def on_item_select(self, _event):
        """一覧選択時に詳細を表示する"""
        selection = self.tree.selection()
        if not selection:
            self.clear_detail()
            return

        row = self.item_row_map.get(selection[0])
        if not row:
            self.clear_detail()
            return

        self.detail_var.set(f"slot_key: {row['slot_key']} / 状態: {row['status_label']}")
        self._set_text(self.plan_text, self.format_plan_detail(row))
        self._set_text(self.actual_text, self.format_actual_detail(row))

    def format_plan_detail(self, row):
        """Spreadsheet の予定案を整形する"""
        return "\n".join(
            [
                f"slot_key: {row['slot_key']}",
                f"日付: {row['target_date'].strftime('%Y-%m-%d')} ({row['weekday_label']}曜日)",
                f"担当: {row['assignee']}",
                f"件名: {row['summary']}",
                f"時間: {row['planned_time_label']}",
                f"場所: {row['location']}",
                "",
                "説明:",
                row["description"],
            ]
        )

    def format_actual_detail(self, row):
        """Google Calendar 上の状態を整形する"""
        if not row["exists"]:
            return "\n".join(
                [
                    "まだカレンダーに作成されていません。",
                    "",
                    "「カレンダーに流し込み」を押すと、",
                    "この予定案を Google Calendar に登録します。",
                ]
            )

        lines = [
            f"イベントID: {row['event_id']}",
            f"件名: {row['actual_summary']}",
            f"時間: {row['actual_start']} - {row['actual_end']}",
            f"場所: {row['actual_location']}",
            "",
            "説明:",
            row["actual_description"],
        ]
        if row["has_changes"]:
            lines.extend(["", "Google Calendar 側で予定内容が編集されています。"])
        return "\n".join(lines)

    def create_events(self):
        """Spreadsheet の予定案を Google Calendar に作成する"""
        try:
            created_count, skipped_count, failed_summaries = create_spreadsheet_demo_events(
                self.calendar_manager,
                self.session_state,
                self.spreadsheet_manager,
            )
        except Exception as exc:
            logger.error("カレンダー流し込みエラー: %s", exc)
            messagebox.showerror("エラー", f"Google Calendar への流し込みに失敗しました:\n{exc}")
            return

        messages = []
        if created_count:
            messages.append(f"{created_count}件の予定を Google Calendar へ作成しました。")
        if skipped_count:
            messages.append(f"{skipped_count}件は既に存在していたためスキップしました。")
        if failed_summaries:
            messages.append(f"作成失敗: {', '.join(failed_summaries)}")
        if not messages:
            messages.append("新しく作成された予定はありません。")

        messagebox.showinfo("流し込み結果", "\n".join(messages))
        self.refresh_rows(show_message=False)

    def flush_events(self):
        """先日付イベントを削除する"""
        if not messagebox.askyesno(
            "確認",
            "現在以降のイベントをカレンダー全体から削除します。続行しますか？",
        ):
            return

        try:
            deleted_count, failed_count = flush_future_events(self.calendar_manager, self.session_state)
        except Exception as exc:
            logger.error("FLUSHエラー: %s", exc)
            messagebox.showerror("エラー", f"FLUSH に失敗しました:\n{exc}")
            return

        lines = [f"先日付イベントを {deleted_count} 件削除しました。"]
        if failed_count:
            lines.append(f"{failed_count} 件の削除に失敗しました。")
        messagebox.showwarning("FLUSH結果", "\n".join(lines))
        self.refresh_rows(show_message=False)


def main():
    """メイン関数"""
    root = tk.Tk()
    SpreadsheetCalendarGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
