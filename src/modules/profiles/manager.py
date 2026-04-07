import os
import random
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger("ProfileManager")

class ProfileManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.profiles_dir = os.path.join(os.getcwd(), 'data', 'browser_profiles')
        os.makedirs(self.profiles_dir, exist_ok=True)

    def get_all_profiles(self):
        query = "SELECT p.id, p.name, p.group_name, pr.ip, pr.port, p.created_at, p.status FROM profiles p LEFT JOIN proxies pr ON p.proxy_id = pr.id"
        return self.db.fetchall(query)

    def get_profiles_by_group(self, group_name):
        if group_name == "All Groups":
            return self.get_all_profiles()
        query = "SELECT p.id, p.name, p.group_name, pr.ip, pr.port, p.created_at, p.status FROM profiles p LEFT JOIN proxies pr ON p.proxy_id = pr.id WHERE p.group_name = ?"
        return self.db.fetchall(query, (group_name,))

    def create_profile(self, name, group_name="Default", proxy_id=None):
        # Basic fingerprinting
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        query = """
            INSERT INTO profiles (name, group_name, proxy_id, user_agent, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (name, group_name, proxy_id, user_agent, datetime.now(), "Ready")

        cursor = self.db.execute(query, params)
        if cursor:
            logger.info(f"Profile created: {name} in group {group_name}")
            return cursor.lastrowid
        return None

    def bulk_create_profiles(self, prefix, count, group_name="Default"):
        created_ids = []
        for i in range(1, count + 1):
            name = f"{prefix}_{i}"
            pid = self.create_profile(name, group_name)
            if pid:
                created_ids.append(pid)
        return created_ids

    def delete_profile(self, profile_id, delete_files=True):
        profile = self.db.fetchone("SELECT name FROM profiles WHERE id = ?", (profile_id,))
        if not profile:
            return False

        name = profile['name']
        query = "DELETE FROM profiles WHERE id = ?"
        if self.db.execute(query, (profile_id,)):
            logger.info(f"Profile deleted from DB: {name}")
            if delete_files:
                import shutil
                profile_path = os.path.join(self.profiles_dir, name)
                if os.path.exists(profile_path):
                    try:
                        shutil.rmtree(profile_path)
                        logger.info(f"Profile files deleted: {profile_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete profile files: {e}")
            return True
        return False

    def update_profile_status(self, profile_id, status):
        query = "UPDATE profiles SET status = ? WHERE id = ?"
        self.db.execute(query, (status, profile_id))

    def get_all_groups(self):
        query = "SELECT DISTINCT group_name FROM profiles WHERE group_name IS NOT NULL"
        rows = self.db.fetchall(query)
        groups = [row['group_name'] for row in rows]
        if "Default" not in groups:
            groups.insert(0, "Default")
        return groups

    def get_profile_by_id(self, profile_id):
         query = "SELECT * FROM profiles WHERE id = ?"
         return self.db.fetchone(query, (profile_id,))

    def scan_profiles(self):
        """Scans the profiles directory and adds missing profiles to the database."""
        added_count = 0
        if os.path.exists(self.profiles_dir):
            for dir_name in os.listdir(self.profiles_dir):
                dir_path = os.path.join(self.profiles_dir, dir_name)
                if os.path.isdir(dir_path):
                    # Check if it exists in DB
                    existing = self.db.fetchone("SELECT id FROM profiles WHERE name = ?", (dir_name,))
                    if not existing:
                        logger.info(f"Found orphaned profile directory: {dir_name}. Adding to DB.")
                        self.create_profile(dir_name, "Imported")
                        added_count += 1
        return added_count

    def cleanup_profile_files(self):
        """Cleans up Cache and Temp files for all profiles in the profiles directory."""
        freed_space = 0
        cleaned_profiles = 0
        import shutil

        if os.path.exists(self.profiles_dir):
            for dir_name in os.listdir(self.profiles_dir):
                dir_path = os.path.join(self.profiles_dir, dir_name)
                if os.path.isdir(dir_path):
                    cache_dir = os.path.join(dir_path, "Default", "Cache")
                    code_cache = os.path.join(dir_path, "Default", "Code Cache")
                    gpu_cache = os.path.join(dir_path, "Default", "GPUCache")

                    cleaned_this_profile = False

                    for target_dir in [cache_dir, code_cache, gpu_cache]:
                        if os.path.exists(target_dir):
                            for item in os.listdir(target_dir):
                                item_path = os.path.join(target_dir, item)
                                try:
                                    size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                    if os.path.isfile(item_path):
                                        os.unlink(item_path)
                                    elif os.path.isdir(item_path):
                                        size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(item_path) for filename in filenames)
                                        shutil.rmtree(item_path)
                                    freed_space += size
                                    cleaned_this_profile = True
                                except Exception as e:
                                    logger.debug(f"Failed to delete {item_path}: {e}")

                    if cleaned_this_profile:
                        cleaned_profiles += 1

        return cleaned_profiles, freed_space
