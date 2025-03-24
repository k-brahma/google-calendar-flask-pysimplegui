import getpass
import os
import shutil
import sys
from pathlib import Path

from encrypt_credentials import encrypt_credentials_folder


def change_encryption_password():
    """暗号化された認証情報のパスワードを変更する"""
    print("=== 認証情報の暗号化パスワード変更 ===")

    # encrypted_credentialsディレクトリの存在を確認
    if not os.path.exists("encrypted_credentials"):
        print("エラー: encrypted_credentialsディレクトリが見つかりません。")
        print("先にencrypt_credentials.pyを実行して認証情報を暗号化してください。")
        return False

    # credentialsディレクトリの存在を確認
    if not os.path.exists("credentials"):
        print("credentialsディレクトリが見つかりません。一時的に作成します。")
        os.makedirs("credentials", exist_ok=True)
        temp_credentials_created = True
    else:
        temp_credentials_created = False

        # 既存のcredentialsディレクトリがある場合は確認
        if os.listdir("credentials"):
            response = input(
                "警告: credentialsディレクトリに既にファイルが存在します。上書きしてもよろしいですか？ (y/n): "
            )
            if response.lower() != "y":
                print("パスワード変更を中止します。")
                return False

    print("\n1. 現在のパスワードを入力してください")
    from crypto_utils import decrypt_file

    # 現在のパスワードを要求
    current_password = getpass.getpass("現在のパスワード: ")

    # 暗号化ファイルを試験的に復号化して、パスワードが正しいか確認
    test_file = None
    for root, _, files in os.walk("encrypted_credentials"):
        for file in files:
            if file.endswith(".encrypted"):
                test_file = os.path.join(root, file)
                break
        if test_file:
            break

    if not test_file:
        print("エラー: 暗号化されたファイルが見つかりません。")
        return False

    try:
        # 一時ファイルに復号化を試みる
        temp_file = "temp_decrypt_test"
        decrypt_file(test_file, current_password, temp_file)
        os.remove(temp_file)  # テストが成功したら削除
        print("現在のパスワードが確認できました。")
    except Exception as e:
        print(f"エラー: 現在のパスワードが正しくありません: {e}")
        return False

    # 暗号化された認証情報を一時的に復号化
    temp_dir = Path("temp_credentials")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    decrypt_count = 0
    for root, _, files in os.walk("encrypted_credentials"):
        rel_path = os.path.relpath(root, "encrypted_credentials")
        for file in files:
            if file.endswith(".encrypted"):
                src_file = os.path.join(root, file)
                # .encryptedの拡張子を削除
                dest_name = file[:-10] if file.endswith(".encrypted") else file
                dest_dir = os.path.join(temp_dir, rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                dest_file = os.path.join(dest_dir, dest_name)

                try:
                    decrypt_file(src_file, current_password, dest_file)
                    decrypt_count += 1
                except Exception as e:
                    print(f"エラー: ファイルの復号化に失敗しました {src_file}: {e}")

    print(f"認証情報の復号化が完了しました。{decrypt_count}ファイルを復号化しました。")

    # 復号化した認証情報をcredentialsディレクトリにコピー
    if os.path.exists("credentials"):
        shutil.rmtree("credentials")
    shutil.copytree(temp_dir, "credentials")

    print("\n2. 新しいパスワードを設定します")

    # 新しいパスワードを要求
    new_password = getpass.getpass("新しいパスワード: ")
    confirm_password = getpass.getpass("新しいパスワードを再入力: ")

    if new_password != confirm_password:
        print("エラー: パスワードが一致しません。パスワード変更を中止します。")
        if temp_credentials_created:
            shutil.rmtree("credentials")
        return False

    # 既存の暗号化ディレクトリをバックアップ
    if os.path.exists("encrypted_credentials.bak"):
        shutil.rmtree("encrypted_credentials.bak")
    shutil.move("encrypted_credentials", "encrypted_credentials.bak")

    # 認証情報を新しいパスワードで暗号化
    result = encrypt_credentials_folder("credentials", new_password)

    if result:
        print("\nパスワードの変更が完了しました。")
        print("バックアップディレクトリ (encrypted_credentials.bak) は安全に削除できます。")
    else:
        print("\nエラー: 新しいパスワードでの暗号化に失敗しました。")
        print("バックアップから元の暗号化ディレクトリを復元します。")
        if os.path.exists("encrypted_credentials"):
            shutil.rmtree("encrypted_credentials")
        shutil.move("encrypted_credentials.bak", "encrypted_credentials")
        return False

    # 一時ディレクトリを削除
    shutil.rmtree(temp_dir)

    # 一時的に作成したcredentialsディレクトリを削除
    if temp_credentials_created:
        shutil.rmtree("credentials")

    return True


if __name__ == "__main__":
    success = change_encryption_password()
    if success:
        print("\n認証情報の暗号化パスワードが正常に変更されました。")
        sys.exit(0)
    else:
        print("\n認証情報の暗号化パスワードの変更に失敗しました。")
        sys.exit(1)
