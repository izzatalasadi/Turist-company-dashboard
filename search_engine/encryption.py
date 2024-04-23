from cryptography.fernet import Fernet
import os

def load_key():
    """
    Load the encryption key from an environment variable or secure storage
    """
    key = os.environ.get('ENCRYPTION_KEY').encode()
    return key

def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    return fernet.decrypt(data.encode()).decode()
