import os
import json
import requests
from src.utils.logger import get_logger

logger = get_logger("ConfigManager")

class ConfigManager:
    def __init__(self):
        self.config_url = "https://example.com/config.json" # Placeholder for Google Drive direct link
        self.local_cache = os.path.join(os.getcwd(), 'data', 'config_cache.json')
        self.config = self._load_config()

    def _load_config(self):
        # Try to fetch from remote
        remote_config = self._fetch_remote_config()
        if remote_config:
            self._save_local_cache(remote_config)
            return remote_config

        # Fallback to local cache
        local_config = self._load_local_cache()
        if local_config:
            logger.warning("Using cached configuration due to remote fetch failure.")
            return local_config

        # Default config if everything fails
        logger.error("Failed to load both remote and cached config. Using default fallback.")
        return self._get_default_config()

    def _fetch_remote_config(self):
        try:
            response = requests.get(self.config_url, timeout=10)
            if response.status_code == 200:
                logger.info("Successfully fetched remote config.")
                return response.json()
            else:
                logger.warning(f"Remote config returned status code {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching remote config: {e}")
            return None

    def _save_local_cache(self, config_data):
        try:
            os.makedirs(os.path.dirname(self.local_cache), exist_ok=True)
            with open(self.local_cache, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save local config cache: {e}")

    def _load_local_cache(self):
        try:
            if os.path.exists(self.local_cache):
                with open(self.local_cache, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load local config cache: {e}")
        return None

    def _get_default_config(self):
        return {
            "version": "1.0.0",
            "whatsapp_number": "+1234567890",
            "buy_link": "https://wa.me/1234567890",
            "banned_uuids": [],
            "selectors": {},
            "auto_update": True
        }

    def get(self, key, default=None):
        return self.config.get(key, default)
