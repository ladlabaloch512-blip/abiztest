import sys
import os
import json
from datetime import datetime, timedelta

# Add parent dir to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.security import SecurityManager
from src.core.licensing import LicenseManager

def generate_local_license(days=30):
    try:
        print("Initializing License Generator...")
        lic_manager = LicenseManager()
        security = SecurityManager()

        # Get the HWID of the current machine
        hwid = lic_manager.get_hwid()
        print(f"Target HWID: {hwid}")

        # Set Expiry
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Setting Expiry: {expiry_str}")

        # Create Payload
        payload = {
            "hwid": hwid,
            "expiry_date": expiry_str
        }

        json_payload = json.dumps(payload)
        encrypted_payload = security.encrypt(json_payload)

        if not encrypted_payload:
            print("Failed to encrypt payload.")
            return

        # Save to file
        os.makedirs(os.path.dirname(lic_manager.license_file), exist_ok=True)
        with open(lic_manager.license_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_payload)

        print(f"\nSUCCESS! License generated and saved to: {lic_manager.license_file}")
        print("You can now run 'python main.py' to access the dashboard.")

    except Exception as e:
        print(f"Error generating license: {e}")

if __name__ == "__main__":
    generate_local_license()
