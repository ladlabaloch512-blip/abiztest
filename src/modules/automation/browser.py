import os
import undetected_chromedriver as uc
from src.utils.logger import get_logger
from src.modules.proxies.manager import ProxyManager

logger = get_logger("BrowserAutomation")

class BrowserManager:
    active_drivers = {}

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
                proxy_info["ip"],
                proxy_info["port"],
                proxy_info["username"],
                proxy_info["password"]
            )
            if ext_path:
                options.add_argument(f"--load-extension={ext_path}")

        try:
            logger.info(f"Launching browser profile: {profile_name}")
            main_version = self._get_chrome_main_version()

            # Use driver_executable_path to reuse driver if already downloaded by UC.
            # UC normally downloads to %APPDATA%\undetected_chromedriver\undetected_chromedriver.exe
            # But sometimes it redownloads if it thinks it's missing or to be safe.
            # We can force it to use a specific path or let UC handle it if we set driver_executable_path.
            driver_dir = uc.patcher.Patcher.data_path
            os.makedirs(driver_dir, exist_ok=True)
            driver_path = os.path.join(driver_dir, f"undetected_chromedriver_{main_version}.exe" if os.name == 'nt' else f"undetected_chromedriver_{main_version}")

            if os.path.exists(driver_path):
                 driver = uc.Chrome(options=options, version_main=main_version, driver_executable_path=driver_path)
            else:
                 driver = uc.Chrome(options=options, version_main=main_version)
                 # After first download, UC saves it to its default roaming path.
                 # Let's find it and copy it to our versioned path for future reuse.
                 default_uc_path = os.path.join(driver_dir, "undetected_chromedriver.exe" if os.name == 'nt' else "undetected_chromedriver")
                 if os.path.exists(default_uc_path) and not os.path.exists(driver_path):
                     import shutil
                     try:
                         shutil.copy2(default_uc_path, driver_path)
                     except Exception as copy_e:
                         logger.debug(f"Could not cache chromedriver: {copy_e}")

            # Handle staged cookies for import
            staged_cookies_path = os.path.join(profile_path, "import_cookies.json")
            if os.path.exists(staged_cookies_path):
                try:
                    import json
                    with open(staged_cookies_path, "r", encoding="utf-8") as f:
                        cookies = json.load(f)

                    # Group cookies by domain to avoid InvalidCookieDomainException
                    cookies_by_domain = {}
                    for cookie in cookies:
                        domain = cookie.get('domain', '')
                        if domain.startswith('.'):
                            domain = domain[1:]
                        if not domain:
                            domain = "google.com" # fallback

                        if domain not in cookies_by_domain:
                            cookies_by_domain[domain] = []
                        cookies_by_domain[domain].append(cookie)

                    for domain, domain_cookies in cookies_by_domain.items():
                        # Navigate to the domain to satisfy Selenium's security policy
                        driver.get(f"https://{domain}")
                        for cookie in domain_cookies:
                            if 'expirationDate' in cookie:
                                cookie['expiry'] = int(cookie['expirationDate'])
                                del cookie['expirationDate']
                            try:
                                driver.add_cookie(cookie)
                            except Exception as ce:
                                logger.debug(f"Failed to set cookie {cookie.get('name')} for {domain}: {ce}")

                    os.remove(staged_cookies_path)
                    logger.info(f"Successfully injected imported cookies for {profile_name}")
                except Exception as e:
                    logger.error(f"Failed to inject cookies for {profile_name}: {e}")

            # Keep a reference so it doesn't get garbage collected immediately
            BrowserManager.active_drivers[profile_name] = driver
            return driver
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return None

    def _get_chrome_main_version(self):
        try:
            import os
            import re

            # Since this is a Windows application, finding Chrome version via subprocess --version doesn't work.
            # We'll check common install paths or registry. For simplicity and robustness, we can try to
            # extract version from the directory structure in Program Files if find_chrome_executable gives us the path.
            chrome_path = uc.find_chrome_executable()
            if not chrome_path:
                return None

            # Usually chrome is in Application\chrome.exe. Next to it is a folder with the version number (e.g. 114.0.5735.90)
            chrome_dir = os.path.dirname(chrome_path)
            for item in os.listdir(chrome_dir):
                if os.path.isdir(os.path.join(chrome_dir, item)):
                    match = re.match(r"^(\d+)\.\d+\.\d+\.\d+$", item)
                    if match:
                        version = int(match.group(1))
                        logger.info(f"Detected Chrome main version from directory: {version}")
                        return version

            # If not found via directory, fallback to Windows registry
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version_str, _ = winreg.QueryValueEx(key, "version")
                match = re.search(r"^(\d+)\.", version_str)
                if match:
                    version = int(match.group(1))
                    logger.info(f"Detected Chrome main version from registry: {version}")
                    return version
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error getting chrome main version: {e}")
        return None
