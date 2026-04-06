import requests
import os
import sys
import shutil
import subprocess
from src.core.config import ConfigManager
from src.utils.logger import get_logger

logger = get_logger("AutoUpdater")

class Updater:
    def __init__(self, current_version="1.0.0"):
        self.current_version = current_version
        self.config = ConfigManager()
        self.temp_dir = os.path.join(os.getcwd(), 'temp_update')

    def check_for_updates(self):
        if not self.config.get("auto_update", True):
            return False, "Auto-update is disabled."

        remote_version = self.config.get("version", self.current_version)
        if remote_version > self.current_version:
            logger.info(f"New version {remote_version} found.")
            return True, remote_version
        return False, "You are on the latest version."

    def download_and_update(self, download_url):
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            new_exe_path = os.path.join(self.temp_dir, "new_update.exe")

            logger.info(f"Downloading update from {download_url}...")
            response = requests.get(download_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(new_exe_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info("Download complete. Triggering update script.")
                self._trigger_replace_script(new_exe_path)
                return True
            else:
                logger.error(f"Failed to download update: Status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error during update: {e}")
            return False

    def _trigger_replace_script(self, new_exe_path):
        # This writes a temporary bat script that waits for the main exe to close,
        # replaces it, and restarts it.
        current_exe = sys.executable
        if not current_exe.endswith('.exe'):
            logger.warning("Not running as an executable. Skipping replace script.")
            return

        bat_path = os.path.join(self.temp_dir, "update.bat")
        bat_content = f"""
        @echo off
        timeout /t 2 /nobreak
        copy /y "{new_exe_path}" "{current_exe}"
        start "" "{current_exe}"
        del "%~f0"
        """
        with open(bat_path, 'w') as f:
            f.write(bat_content)

        subprocess.Popen(bat_path, shell=True)
        sys.exit(0)
