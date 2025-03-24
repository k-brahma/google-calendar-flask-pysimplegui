import getpass
import os
import sys
from pathlib import Path

from crypto_utils import encrypt_file


def encrypt_credentials_folder(credentials_dir, password=None):
    """認証情報ディレクトリの内容を暗号化する"""
    credentials_path = Path(credentials_dir)

    if not credentials_path.exists() or not credentials_path.is_dir():
        print(f"エラー: {credentials_dir} が見つからないか、ディレクトリではありません。")
        return False

    # パスワードが指定されていない場合は入力を求める
    if password is None:
        password = getpass.getpass("暗号化パスワードを入力してください: ")
        confirm_password = getpass.getpass("パスワードを再入力してください: ")
        if password != confirm_password:
            print("パスワードが一致しません。暗号化を中止します。")
            return False

    # 暗号化済みファイルを保存するディレクトリを作成
    encrypted_dir = credentials_path.parent / "encrypted_credentials"
    os.makedirs(encrypted_dir, exist_ok=True)

    # 各ファイルを暗号化
    file_count = 0
    for file_path in credentials_path.glob("**/*"):
        if file_path.is_file():
            # 相対パスを維持する
            rel_path = file_path.relative_to(credentials_path)
            encrypted_file_path = encrypted_dir / f"{rel_path}.encrypted"

            # 出力ディレクトリがなければ作成
            os.makedirs(encrypted_file_path.parent, exist_ok=True)

            # ファイルを暗号化
            encrypt_file(file_path, password, encrypted_file_path)
            file_count += 1
            print(f"暗号化: {file_path} → {encrypted_file_path}")

    # パスワードを保存するファイルを作成（本番では使用しないでください！）
    # これはテスト用で、実際のアプリケーションではユーザーに直接入力させるべきです
    with open(encrypted_dir / "password.txt", "w") as f:
        f.write("このファイルには本番環境では実際のパスワードを保存しないでください！\n")
        f.write("テスト用パスワード: " + password)

    print(f"\n暗号化完了: {file_count}ファイルを暗号化しました。")
    print(f"暗号化されたファイルは {encrypted_dir} に保存されました。")
    print(
        "\n注意: PyInstallerでアプリをビルドする際に、このencrypted_credentialsディレクトリを含めてください。"
    )
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        credentials_dir = sys.argv[1]
    else:
        credentials_dir = "credentials"

    encrypt_credentials_folder(credentials_dir)
