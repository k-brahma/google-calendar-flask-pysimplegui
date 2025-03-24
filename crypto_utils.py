import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# パスワードからキーを生成する関数
def generate_key_from_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)

    # パスワードをバイト列に変換
    if isinstance(password, str):
        password = password.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key, salt


# ファイルを暗号化する関数
def encrypt_file(file_path, password, output_path=None):
    if output_path is None:
        output_path = file_path + ".encrypted"

    # パスワードからキーを生成
    key, salt = generate_key_from_password(password)

    # ファイルデータを読み込む
    with open(file_path, "rb") as file:
        data = file.read()

    # 暗号化
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)

    # 暗号化データとソルトを保存
    with open(output_path, "wb") as file:
        file.write(salt)  # 最初の16バイトがソルト
        file.write(encrypted_data)

    return output_path


# ファイルを復号化する関数
def decrypt_file(encrypted_file_path, password, output_path=None):
    # 暗号化データを読み込む
    with open(encrypted_file_path, "rb") as file:
        file_data = file.read()

    # ソルトと暗号化データを分離
    salt = file_data[:16]
    encrypted_data = file_data[16:]

    # パスワードからキーを再生成
    key, _ = generate_key_from_password(password, salt)

    # 復号化
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)

    # 復号化データを保存または返す
    if output_path:
        with open(output_path, "wb") as file:
            file.write(decrypted_data)
        return output_path
    else:
        return decrypted_data


# 文字列データを暗号化する関数
def encrypt_data(data, password):
    if isinstance(data, str):
        data = data.encode()

    key, salt = generate_key_from_password(password)
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)

    # ソルトと暗号化データを結合
    return salt + encrypted_data


# 暗号化された文字列データを復号化する関数
def decrypt_data(encrypted_data, password):
    # ソルトと暗号化データを分離
    salt = encrypted_data[:16]
    actual_encrypted_data = encrypted_data[16:]

    key, _ = generate_key_from_password(password, salt)
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(actual_encrypted_data)

    return decrypted_data
