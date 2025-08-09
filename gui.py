import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from tkcalendar import DateEntry
from gcal.calendar_manager import CalendarManager

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CalendarGUI:
    def __init__(self, root):
        """カレンダーGUIアプリケーションの初期化"""
        self.root = root
        self.root.title("Google Calendar GUI (Tkinter)")
        self.root.geometry("1000x700")
        
        # カレンダーマネージャーの初期化
        try:
            self.calendar_manager = CalendarManager()
        except Exception as e:
            logger.error(f"CalendarManager初期化エラー: {e}")
            messagebox.showerror("エラー", f"カレンダーマネージャーの初期化に失敗しました:\n{e}")
            return
        
        # データ
        self.df = pd.DataFrame()
        self.current_event_id = None
        self.item_id_map = {}  # TreeviewアイテムとIDのマッピング
        
        # GUI作成
        self.create_widgets()
        self.load_events()
    
    def get_events_df(self):
        """カレンダーイベントをDataFrameとして取得"""
        JST = ZoneInfo("Asia/Tokyo")
        time_min = datetime.now(JST)
        time_max = time_min + timedelta(days=30)

        # UTC（Z）に変換
        time_min_utc = time_min.astimezone(ZoneInfo("UTC"))
        time_max_utc = time_max.astimezone(ZoneInfo("UTC"))

        try:
            events = self.calendar_manager.get_events(
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
                    # 日付書式をyyyy/mm/dd形式に変更
                    if len(start_time) >= 10 and start_time[4] == '-' and start_time[7] == '-':
                        start_time = start_time.replace('-', '/', 2)

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
        except Exception as e:
            logger.error(f"イベント取得エラー: {e}")
            messagebox.showerror("エラー", f"イベントの取得に失敗しました:\n{e}")
            return pd.DataFrame()
    
    def create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ヘッダーフレーム
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # タイトル
        title_label = ttk.Label(header_frame, text="Google Calendar イベント一覧", font=("Arial", 16))
        title_label.pack(side=tk.LEFT)
        
        # ボタンフレーム
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.refresh_button = ttk.Button(button_frame, text="最新の状態を取得", command=self.refresh_events)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.exit_button = ttk.Button(button_frame, text="終了", command=self.root.quit)
        self.exit_button.pack(side=tk.LEFT)
        
        # テーブルフレーム
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeviewでテーブル作成
        self.tree = ttk.Treeview(table_frame, show='headings', selectmode='extended')
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # テーブルの配置
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # イベント選択時のコールバック
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        
        # 編集フレーム
        self.create_edit_frame(main_frame)
    
    def create_edit_frame(self, parent):
        """編集フレームの作成"""
        edit_frame = ttk.LabelFrame(parent, text="イベント詳細")
        edit_frame.pack(fill=tk.X, pady=(10, 0))
        
        # グリッド設定
        edit_frame.grid_columnconfigure(1, weight=1)
        
        # タイトル
        ttk.Label(edit_frame, text="タイトル:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.title_entry = ttk.Entry(edit_frame, width=50)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # 開始日時
        ttk.Label(edit_frame, text="開始日:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        start_frame = ttk.Frame(edit_frame)
        start_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.start_date_entry = DateEntry(start_frame, width=12, background='darkblue',
                                         foreground='white', borderwidth=2,
                                         date_pattern='yyyy/mm/dd')
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(start_frame, text="時刻:").pack(side=tk.LEFT)
        self.start_time_entry = ttk.Entry(start_frame, width=8)
        self.start_time_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 終了日時
        ttk.Label(edit_frame, text="終了日:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        end_frame = ttk.Frame(edit_frame)
        end_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.end_date_entry = DateEntry(end_frame, width=12, background='darkblue',
                                       foreground='white', borderwidth=2,
                                       date_pattern='yyyy/mm/dd')
        self.end_date_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(end_frame, text="時刻:").pack(side=tk.LEFT)
        self.end_time_entry = ttk.Entry(end_frame, width=8)
        self.end_time_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 場所
        ttk.Label(edit_frame, text="場所:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.location_entry = ttk.Entry(edit_frame, width=50)
        self.location_entry.grid(row=3, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # 説明
        ttk.Label(edit_frame, text="説明:").grid(row=4, column=0, sticky=tk.NW, padx=5, pady=5)
        self.description_text = tk.Text(edit_frame, width=50, height=5)
        self.description_text.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.save_button = ttk.Button(button_frame, text="保存", command=self.save_event)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(button_frame, text="削除", command=self.delete_event)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="キャンセル", command=self.clear_form)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.new_button = ttk.Button(button_frame, text="新規作成", command=self.new_event)
        self.new_button.pack(side=tk.RIGHT, padx=5)
    
    def load_events(self):
        """イベントをロードしてテーブルに表示"""
        self.df = self.get_events_df()
        self.update_table()
    
    def update_table(self):
        """テーブルの更新"""
        # 既存の項目をクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.df.empty:
            return
        
        # ヘッダーの設定（IDを除外）
        display_columns = [col for col in self.df.columns if col != "ID"]
        self.tree['columns'] = display_columns
        
        for col in display_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, minwidth=100)
        
        # IDとTreeviewアイテムのマッピングを初期化
        self.item_id_map = {}
        
        # データの挿入
        for index, row in self.df.iterrows():
            display_values = [row[col] for col in display_columns]
            item_id = self.tree.insert('', 'end', values=display_values)
            # IDとTreeviewアイテムのマッピングを保存
            self.item_id_map[item_id] = row['ID']
    
    def on_item_select(self, event):
        """テーブル項目選択時の処理"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # マッピングからIDを取得
        event_id = self.item_id_map.get(item)
        
        if not event_id:
            return
        
        # DataFrameから詳細情報を取得
        event_row = self.df[self.df['ID'] == event_id].iloc[0]
        
        # 詳細情報を取得
        try:
            selected_event = self.calendar_manager.get_event(event_id)
            end_time = ""
            full_description = ""
            
            if selected_event:
                if "end" in selected_event:
                    end_time = selected_event["end"].get(
                        "dateTime", selected_event["end"].get("date", "")
                    )
                    if "T" in end_time:  # datetime形式の場合
                        end_time = end_time.replace("T", " ").replace(":00+09:00", "")
                        # 日付書式をyyyy/mm/dd形式に変更
                        if len(end_time) >= 10 and end_time[4] == '-' and end_time[7] == '-':
                            end_time = end_time.replace('-', '/', 2)
                
                full_description = selected_event.get("description", "")
            
            # フォームに値を設定
            self.current_event_id = event_id
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, event_row['タイトル'])
            
            # 開始時間の設定
            start_datetime_str = event_row['開始時間']
            if start_datetime_str and ' ' in start_datetime_str:
                start_date_str, start_time_str = start_datetime_str.split(' ', 1)
                try:
                    # yyyy/mm/dd形式に対応
                    if '/' in start_date_str:
                        start_date = datetime.strptime(start_date_str, '%Y/%m/%d').date()
                    else:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    self.start_date_entry.set_date(start_date)
                    self.start_time_entry.delete(0, tk.END)
                    self.start_time_entry.insert(0, start_time_str)
                except ValueError:
                    pass
            
            # 終了時間の設定
            if end_time and ' ' in end_time:
                end_date_str, end_time_str = end_time.split(' ', 1)
                try:
                    # yyyy/mm/dd形式に対応
                    if '/' in end_date_str:
                        end_date = datetime.strptime(end_date_str, '%Y/%m/%d').date()
                    else:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    self.end_date_entry.set_date(end_date)
                    self.end_time_entry.delete(0, tk.END)
                    self.end_time_entry.insert(0, end_time_str)
                except ValueError:
                    pass
            
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, event_row['場所'])
            
            self.description_text.delete('1.0', tk.END)
            self.description_text.insert('1.0', full_description)
            
            logger.info(f"選択されたイベント - ID: {event_id}, タイトル: {event_row['タイトル']}")
            
        except Exception as e:
            logger.error(f"イベント詳細取得エラー: {e}")
            messagebox.showerror("エラー", f"イベント詳細の取得に失敗しました:\n{e}")
    
    def clear_form(self):
        """フォームのクリア"""
        self.current_event_id = None
        self.title_entry.delete(0, tk.END)
        self.start_date_entry.set_date(datetime.now().date())
        self.start_time_entry.delete(0, tk.END)
        self.end_date_entry.set_date(datetime.now().date())
        self.end_time_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.description_text.delete('1.0', tk.END)
    
    def new_event(self):
        """新規イベント作成の準備"""
        self.clear_form()
        
        # 現在時刻から1時間後の時間を設定（デフォルト）
        default_time = datetime.now() + timedelta(hours=1)
        self.start_date_entry.set_date(default_time.date())
        self.start_time_entry.insert(0, default_time.strftime("%H:%M"))
        
        end_time = default_time + timedelta(hours=1)
        self.end_date_entry.set_date(end_time.date())
        self.end_time_entry.insert(0, end_time.strftime("%H:%M"))
    
    def save_event(self):
        """イベントの保存"""
        try:
            # フォームからデータを取得
            title = self.title_entry.get().strip()
            start_date = self.start_date_entry.get_date()
            start_time_str = self.start_time_entry.get().strip()
            end_date = self.end_date_entry.get_date()
            end_time_str = self.end_time_entry.get().strip()
            location = self.location_entry.get().strip()
            description = self.description_text.get('1.0', tk.END).strip()
            
            # バリデーション
            if not title:
                messagebox.showerror("エラー", "タイトルを入力してください")
                return
            
            if not start_time_str:
                messagebox.showerror("エラー", "開始時刻を入力してください")
                return
            
            # 時間の解析
            try:
                # 開始時間の解析
                start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
                start_time = datetime.combine(start_date, start_time_obj)
                
                # 終了時間の解析
                if end_time_str:
                    end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
                    end_time = datetime.combine(end_date, end_time_obj)
                    if end_time <= start_time:
                        messagebox.showerror("エラー", "終了時間は開始時間より後にしてください")
                        return
                else:
                    end_time = start_time + timedelta(hours=1)
            except ValueError:
                messagebox.showerror("エラー", "時刻の形式が正しくありません。\n例: 09:00")
                return
            
            # イベントの作成または更新
            if self.current_event_id:
                # 既存イベントの更新
                logger.info(f"イベント更新 - ID: {self.current_event_id}")
                updated_event = self.calendar_manager.update_event(
                    event_id=self.current_event_id,
                    summary=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    location=location,
                )
                
                if updated_event:
                    messagebox.showinfo("完了", "イベントを更新しました")
                else:
                    messagebox.showerror("エラー", "イベントの更新に失敗しました")
            else:
                # 新規イベントの作成
                logger.info(f"イベント新規作成 - タイトル: {title}")
                created_event = self.calendar_manager.create_event(
                    summary=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    location=location,
                )
                
                if created_event:
                    messagebox.showinfo("完了", "イベントを作成しました")
                else:
                    messagebox.showerror("エラー", "イベントの作成に失敗しました")
            
            # イベントリストを更新
            self.load_events()
            self.clear_form()
            
        except Exception as e:
            logger.error(f"イベント保存エラー: {e}")
            messagebox.showerror("エラー", f"イベント保存中にエラーが発生しました:\n{e}")
    
    def delete_event(self):
        """イベントの削除"""
        if not self.current_event_id:
            messagebox.showwarning("警告", "削除するイベントが選択されていません")
            return
        
        # 削除確認ダイアログ
        if not messagebox.askyesno("確認", "選択したイベントを削除しますか？"):
            return
        
        try:
            logger.info(f"イベント削除 - ID: {self.current_event_id}")
            
            if self.calendar_manager.delete_event(self.current_event_id):
                messagebox.showinfo("完了", "イベントを削除しました")
                # イベントリストを更新
                self.load_events()
                self.clear_form()
            else:
                messagebox.showerror("エラー", "イベントの削除に失敗しました")
                
        except Exception as e:
            logger.error(f"イベント削除エラー: {e}")
            messagebox.showerror("エラー", f"イベント削除中にエラーが発生しました:\n{e}")
    
    def refresh_events(self):
        """イベントの再読み込み"""
        self.load_events()
        self.clear_form()
        messagebox.showinfo("完了", "イベントを更新しました")


def main():
    """メイン関数"""
    root = tk.Tk()
    CalendarGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
