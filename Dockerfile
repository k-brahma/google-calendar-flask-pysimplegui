# ベースイメージとしてPython 3.11を使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    tk \
    && rm -rf /var/lib/apt/lists/*

# 必要なPythonライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# デフォルトでは5000番ポートを公開してFlaskアプリを実行
EXPOSE 5000

# 環境変数でFlaskに外部からのアクセスを許可
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# コンテナ起動時のコマンド
CMD ["flask", "run"]

# 別のコマンドでGUIアプリケーションを実行する場合
# 注意: GUIアプリはコンテナ内で実行する場合はX11転送などが必要
# CMD ["python", "gui.py"] 