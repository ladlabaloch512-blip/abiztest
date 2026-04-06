import os
import undetected_chromedriver as uc
from src.utils.logger import get_logger
from src.modules.proxies.manager import ProxyManager

logger = get_logger("BrowserAutomation")

class BrowserManager:
    def __init__(self):
        self.profiles_dir = os.path.join(os.getcwd(), 'data', 'browser_profiles')
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.proxy_manager = ProxyManager()

    def launch_profile(self, profile_name, proxy_info=None):
        profile_path = os.path.join(self.profiles_dir, profile_name)

        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")

        # Apply proxy if provided
        if proxy_info:
            ext_path = self.proxy_manager.generate_proxy_extension(
                profile_name,
                proxy_info.get("ip"),
                proxy_info.get("port"),
                proxy_info.get("username"),
                proxy_info.get("password")
            )
            if ext_path:
                options.add_extension(ext_path)

        try:
            logger.info(f"Launching browser profile: {profile_name}")
            driver = uc.Chrome(options=options, version_main=self._get_chrome_main_version())
            return driver
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return None

    def _get_chrome_main_version(self):
        # Optional: Implement logic to dynamically find installed Chrome version.
        # Fallback to returning None so undetected_chromedriver tries to find it automatically.
        return None
