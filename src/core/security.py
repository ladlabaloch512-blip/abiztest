import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.utils.logger import get_logger

logger = get_logger("Security")

class SecurityManager:
    def __init__(self, key_salt=b"FB_MARKETPLACE_SALT"):
        self.salt = key_salt
        self.fernet = self._generate_fernet("STATIC_SECRET_KEY_REPLACE_LATER")

    def _generate_fernet(self, password_str):
        try:
            password = password_str.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            return Fernet(key)
        except Exception as e:
            logger.error(f"Failed to generate Fernet key: {e}")
            return None

    def encrypt(self, data: str) -> str:
        if not self.fernet: return ""
        try:
            return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ""

    def decrypt(self, encrypted_data: str) -> str:
        if not self.fernet: return ""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
