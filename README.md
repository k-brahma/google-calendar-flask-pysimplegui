# Google Calendar 操作アプリ

このプロジェクトはGoogle Calendar の操作を行うデモです。

Flaskを使用したウェブアプリケーションと、PySimpleGUIを使用したデスクトップGUIアプリケーションの2つのインターフェースを提供しています。  
どちらも同じGoogle Calendar APIを使用して、イベントの閲覧・作成・編集・削除を行うことができます。

## セットアップ方法

1. 必要なライブラリをインストールします：

```bash
pip install -r requirements.txt
```

2. 認証情報を取得し、`credentials/credentials.json`に保存します。
   - Google Cloud Platformで作成したプロジェクトから認証情報を取得してください。

## 認証の問題と解決方法

認証時に「アプリはGoogle の審査プロセスを完了していません」というエラーが表示される場合：

1. Google Cloud Platformのコンソールにアクセス
2. プロジェクトを選択
3. 「APIとサービス」→「OAuth同意画面」を選択
4. 以下のいずれかの方法で対応：
   - **テストユーザーを追加**: 自分のGoogleアカウントをテストユーザーとして追加
   - **本番環境に公開**: 同意画面の設定で「本番環境に公開」を選択（公開審査が必要）

## 実行方法

基本的な認証情報チェック：
```bash
python test_calendar_connection_simple.py
```

完全な接続テスト（OAuth認証が必要）：
```bash
python test_calendar_connection.py
```

## Google Cloud Platform（GCP）でのサービスアカウント設定

1. GCPコンソールでプロジェクトを作成
2. Google Calendar APIを有効化
3. サービスアカウントを作成（IAM & 管理 > サービスアカウント）
4. サービスアカウントキー（JSON形式）を作成してダウンロード
5. 共有したいGoogleカレンダーの設定で、作成したサービスアカウントのメールアドレスと共有

## 認証情報の設定

サービスアカウントキーを`credentials/`ディレクトリに配置し、`credentials/config.json`ファイルを設定します。

config.jsonサンプル:
```json
{
  "auth_settings": {
    "impersonation_email": "your-email@example.com"
  },
  "calendar_settings": {
    "timezone": "Asia/Tokyo",
    "default_calendar_id": "primary",
    "target_calendar_id": "your-calendar-id@group.calendar.google.com"
  }
}
```

## Flaskウェブアプリケーション

このプロジェクトのメインインターフェースとして、Flaskを使用したウェブアプリケーションを提供しています。

### 機能

- イベント一覧表示：カレンダーから30日分のイベントを表示
- イベント詳細表示：個別のイベント情報を表示
- イベント作成：新規イベントの作成フォーム
- イベント編集：既存イベントの詳細を編集
- イベント削除：不要なイベントの削除

### 実行方法

Flaskアプリケーションを起動するには：

```bash
python app.py
```

ブラウザで以下のURLにアクセスします：
```
http://localhost:5000
```

## GUIアプリケーション

補助的なインターフェースとして、PySimpleGUIを使用したデスクトップGUIアプリケーションも提供しています。

### 前提条件

- Python 3.11以上がインストールされていること
- tkinterがインストールされていること（Python 3.13.2以上の場合は標準でインストール済み）

### インストール手順

1. リポジトリをクローンまたはダウンロードします

2. 必要なライブラリをインストールします：
```bash
pip install -r requirements.txt
```

3. PySimpleGUIについて：
   - このリポジトリには既に`PySimpleGUI.py`が含まれているため、追加のインストールは不要です
   - もし問題が発生した場合は、以下のリポジトリから最新版を取得することもできます：
     ```bash
     git clone https://github.com/andor-pierdelacabeza/PySimpleGUI-4-foss.git
     cp PySimpleGUI-4-foss/PySimpleGUI.py .
     rm -rf PySimpleGUI-4-foss  # クローンしたリポジトリの削除
     ```

### 実行方法

GUIアプリケーションを起動するには：

```bash
python gui.py
```

### 機能

- イベント一覧の表示：カレンダーから30日分のイベントを表示
- イベントの詳細表示：リストからイベントをクリックすると詳細を表示
- 新規イベント作成：「新規作成」ボタンでイベントを作成
- イベント編集：既存イベントの詳細を変更して「保存」
- イベント削除：「削除」ボタンで選択中のイベントを削除

### トラブルシューティング

- **tkinterエラー**：Python 3.13.0を使用している場合、3.13.2以上にアップグレードするか、別途tkinterをインストールしてください
- **認証エラー**：サービスアカウントキーファイルと設定ファイルが正しく配置されているか確認してください

## ディレクトリ構造

```
calendar-gui/
├── app.py               # Flaskアプリケーションのメインファイル
├── gui.py               # PySimpleGUIアプリケーションのメインファイル
├── PySimpleGUI.py       # PySimpleGUIライブラリ
├── README.md            # このファイル
├── requirements.txt     # 必要なライブラリリスト
├── credentials/         # 認証情報ディレクトリ
│   ├── config.json      # 設定ファイル
│   └── credentials.json # 認証情報ファイル
└── templates/           # Flaskテンプレートディレクトリ
    ├── base.html        # ベーステンプレート
    ├── index.html       # イベント一覧表示
    ├── event.html       # イベント詳細表示
    ├── create.html      # イベント作成フォーム
    └── edit.html        # イベント編集フォーム
```

## Dockerでの実行

このプロジェクトはDockerを使用して環境を簡単に構築することもできます。

### Dockerイメージのビルド

```bash
docker build -t calendar-flask-gui-app .
```

### Flaskアプリケーションの実行

```bash
docker run -p 5000:5000 -v $(pwd)/credentials:/app/credentials calendar-flask-gui-app
```

Windows PowerShellの場合:
```powershell
docker run -p 5000:5000 -v ${PWD}/credentials:/app/credentials calendar-flask-gui-app
```

### GUIアプリケーションの実行（X11転送が必要）

Linuxの場合:
```bash
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v $(pwd)/credentials:/app/credentials calendar-flask-gui-app python gui.py
```

注意: Docker内でのGUIアプリケーションの実行は、特にWindows環境では複雑な設定が必要になります。基本的にはDockerではFlaskウェブアプリを使用し、GUIアプリケーションを直接実行することをお勧めします。 