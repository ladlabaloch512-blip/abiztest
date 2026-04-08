import os
import zipfile
import requests
from src.utils.logger import get_logger
from src.database.db_manager import DatabaseManager

logger = get_logger("ProxyManager")

class ProxyManager:
    def __init__(self):
        self.extensions_dir = os.path.join(os.getcwd(), 'data', 'proxy_extensions')
        os.makedirs(self.extensions_dir, exist_ok=True)
        self.db = DatabaseManager()

    def generate_proxy_extension(self, proxy_id, proxy_host, proxy_port, proxy_user, proxy_pass):
        """
        Creates a dynamic Chrome extension to handle authenticated proxies.
        """
        extension_path = os.path.join(self.extensions_dir, f"proxy_{proxy_id}.zip")
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "storage",
                "webRequest",
                "webRequestAuthProvider"
            ],
            "host_permissions": [
                "<all_urls>"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "minimum_chrome_version":"88.0.0"
        }
        """

        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy_host}",
                    port: parseInt({proxy_port})
                }},
                bypassList: ["localhost"]
            }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details, callback) {{
            callback({{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }});
        }}
        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['asyncBlocking']
        );
        """

        try:
            # undetected_chromedriver prefers loading unpacked extensions
            extension_dir = os.path.join(self.extensions_dir, f"proxy_{proxy_id}")
            os.makedirs(extension_dir, exist_ok=True)

            with open(os.path.join(extension_dir, "manifest.json"), "w", encoding="utf-8") as f:
                f.write(manifest_json)

            with open(os.path.join(extension_dir, "background.js"), "w", encoding="utf-8") as f:
                f.write(background_js)

            return extension_dir
        except Exception as e:
            logger.error(f"Failed to create proxy extension: {e}")
            return None

    def add_proxy(self, ip, port, username=None, password=None):
        query = """
            INSERT INTO proxies (ip, port, username, password, status)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (ip, port, username, password, "Untested")
        cursor = self.db.execute(query, params)
        if cursor:
            logger.info(f"Proxy added: {ip}:{port}")
            return cursor.lastrowid
        return None

    def get_all_proxies(self):
        return self.db.fetchall("SELECT * FROM proxies")

    def delete_proxy(self, proxy_id):
        # Remove proxy from profiles first
        self.db.execute("UPDATE profiles SET proxy_id = NULL WHERE proxy_id = ?", (proxy_id,))
        return self.db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,)) is not None

    def assign_proxy_to_profile(self, profile_id, proxy_id):
        query = "UPDATE profiles SET proxy_id = ? WHERE id = ?"
        return self.db.execute(query, (proxy_id, profile_id)) is not None

    def get_proxy_by_id(self, proxy_id):
        query = "SELECT * FROM proxies WHERE id = ?"
        return self.db.fetchone(query, (proxy_id,))

    def test_proxy(self, proxy_str):
        # proxy_str format: ip:port:user:pass
        try:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                ip, port, user, password = parts
                proxies = {
                    "http": f"http://{user}:{password}@{ip}:{port}",
                    "https": f"http://{user}:{password}@{ip}:{port}"
                }
            elif len(parts) == 2:
                ip, port = parts
                proxies = {
                    "http": f"http://{ip}:{port}",
                    "https": f"http://{ip}:{port}"
                }
            else:
                return False, "Invalid format"

            response = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True, response.json().get("ip")
            return False, "Failed to connect"
        except Exception as e:
            return False, str(e)
