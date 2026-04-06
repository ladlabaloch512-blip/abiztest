import uuid
import json
import os
from datetime import datetime
from src.core.security import SecurityManager
from src.core.config import ConfigManager
from src.utils.logger import get_logger

logger = get_logger("Licensing")

class LicenseManager:
    def __init__(self):
        self.security = SecurityManager()
        self.config = ConfigManager()
        self.license_file = os.path.join(os.getcwd(), 'data', 'license.lic')
        self.hwid = self._generate_hwid()

    def _generate_hwid(self):
        # Generates a stable hardware ID.
        # For a truly secure system, this should query motherboard/disk serials via WMI on Windows.
        # Here we use uuid.getnode() as a basic cross-platform implementation.
        mac = uuid.getnode()
        hwid_raw = f"HWID-{mac}"
        # A simple hash to obscure it
        return self.security.encrypt(hwid_raw)[:32]

    def get_hwid(self):
        return self.hwid

    def check_license(self):
        # 1. Check if HWID is banned in remote config
        banned_list = self.config.get("banned_uuids", [])
        if self.hwid in banned_list:
            logger.warning(f"HWID {self.hwid} is globally banned.")
            return False, "Your hardware ID is banned. Contact support."

        # 2. Check local license file
        if not os.path.exists(self.license_file):
            return False, "License file not found."

        try:
            with open(self.license_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()

            decrypted_data = self.security.decrypt(encrypted_data)
            if not decrypted_data:
                return False, "Invalid or corrupted license file."

            license_info = json.loads(decrypted_data)

            # Verify HWID
            if license_info.get("hwid") != self.hwid:
                return False, "License is not bound to this machine."

            # Verify Expiry
            expiry_str = license_info.get("expiry_date")
            if not expiry_str:
                return False, "Invalid license format."

            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expiry_date:
                return False, "License has expired."

            return True, f"Valid license until {expiry_str}"

        except Exception as e:
            logger.error(f"License check failed: {e}")
            return False, "Error validating license."
