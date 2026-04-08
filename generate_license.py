import json
import os
from datetime import datetime, timedelta
from src.core.security import SecurityManager
from src.core.licensing import LicenseManager

security = SecurityManager()
lm = LicenseManager()
hwid = lm.get_hwid()

payload = {
    "hwid": hwid,
    "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
}

json_payload = json.dumps(payload)
encrypted_payload = security.encrypt(json_payload)

save_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'license.lic'))
os.makedirs(os.path.dirname(save_path), exist_ok=True)
with open(save_path, 'w', encoding='utf-8') as f:
    f.write(encrypted_payload)

print(f"Generated license for HWID: {hwid}")
