import os
from cryptography.fernet import Fernet


def encrypt_wallet_secret(data):
    key = os.environ.get("KEY")
    f = Fernet(key)
    return f.encrypt(data.encode()).decode("utf-8")


def decrypt_wallet_secret(data):
    key = os.environ.get("KEY")
    print(f'seceret stored {data}')
    print(key)
    f = Fernet(key)
    return f.decrypt(data.encode()).decode("utf-8")
