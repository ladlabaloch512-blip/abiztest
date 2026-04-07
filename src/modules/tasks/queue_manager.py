from concurrent.futures import ThreadPoolExecutor
import time
import eel
from src.utils.logger import get_logger

logger = get_logger("TaskQueue")

class BrowserLaunchTask:
    def __init__(self, profile_id, profile_name, proxy_info=None, custom_url=None, external_path=None, automation_callback=None):
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.proxy_info = proxy_info
        self.custom_url = custom_url
        self.external_path = external_path
        self.automation_callback = automation_callback
        self.task_id = f"launch_{self.profile_name}"

    def run(self):
        try:
            from src.modules.automation.browser import BrowserManager
            logger.info(f"Task started: Launching {self.profile_name}")

            browser_mgr = BrowserManager()
            driver = browser_mgr.launch_profile(self.profile_name, self.proxy_info, self.external_path)

            if driver:
                try:
                    eel.update_profile_status(self.profile_id, "Running")()
                except Exception:
                    pass

                if self.custom_url:
                    try:
                        url = self.custom_url
                        if not url.startswith("http://") and not url.startswith("https://"):
                            url = "https://" + url
                        driver.get(url)
                    except Exception as e:
                        logger.error(f"Failed to load custom URL {self.custom_url}: {e}")


                # Execute Selenium automation directly in this background thread
                if self.automation_callback:
                    try:
                        self.automation_callback(driver)
                    except Exception as ac_err:
                        logger.error(f"Automation callback failed for {self.profile_name}: {ac_err}")
                # Now wait for the driver to be manually closed
                try:
                    while True:
                        # Will raise exception if driver window is closed/killed
                        _ = driver.title
                        time.sleep(1)
                except Exception:
                    logger.info(f"Browser profile {self.profile_name} closed.")
                finally:
                    # Clean up reference
                    if self.profile_name in BrowserManager.active_drivers:
                        del BrowserManager.active_drivers[self.profile_name]
                    try:
                        driver.quit()
                    except:
                        pass

                    # Perform deep auto-cleanup immediately to save disk space
                    try:
                        import os
                        from src.modules.profiles.manager import ProfileManager
                        if self.external_path:
                            profile_dir = os.path.join(self.external_path, self.profile_name)
                        else:
                            profile_dir = os.path.join(os.getcwd(), 'data', 'browser_profiles', self.profile_name)

                        if os.path.exists(profile_dir):
                            ProfileManager.cleanup_single_profile_path(profile_dir)
                            logger.info(f"Auto-cleanup completed for {self.profile_name}.")
                    except Exception as clean_err:
                        logger.debug(f"Auto-cleanup failed for {self.profile_name}: {clean_err}")

                try:
                    eel.update_profile_status(self.profile_id, "Ready")()
                except Exception:
                    pass
            else:
                try:
                    eel.update_profile_status(self.profile_id, "Failed")()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error in BrowserLaunchTask: {e}")
            try:
                eel.update_profile_status(self.profile_id, "Error")()
            except Exception:
                pass


class TaskQueueManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskQueueManager, cls).__new__(cls)
            cls._instance.threadpool = ThreadPoolExecutor(max_workers=50)
            logger.info("Task Queue initialized. Max threads: 50")
        return cls._instance

    def set_max_threads(self, max_threads):
        # ThreadPoolExecutor cannot have its max_workers changed dynamically after creation easily.
        # We will create a new pool if needed.
        self.threadpool.shutdown(wait=False)
        self.threadpool = ThreadPoolExecutor(max_workers=max_threads)
        logger.info(f"Task Queue Max threads updated to: {max_threads}")

    def add_task(self, runnable_task):
        self.threadpool.submit(runnable_task.run)
