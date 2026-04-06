import os
import zipfile
import requests
from src.utils.logger import get_logger

logger = get_logger("ProxyManager")

class ProxyManager:
    def __init__(self):
        self.extensions_dir = os.path.join(os.getcwd(), 'data', 'proxy_extensions')
        os.makedirs(self.extensions_dir, exist_ok=True)

    def generate_proxy_extension(self, proxy_id, proxy_host, proxy_port, proxy_user, proxy_pass):
        """
        Creates a dynamic Chrome extension to handle authenticated proxies.
        """
        extension_path = os.path.join(self.extensions_dir, f"proxy_{proxy_id}.zip")
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
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
        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }};
        }}
        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        try:
            with zipfile.ZipFile(extension_path, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            return extension_path
        except Exception as e:
            logger.error(f"Failed to create proxy extension: {e}")
            return None

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
