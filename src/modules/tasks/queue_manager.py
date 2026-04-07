from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot
from src.utils.logger import get_logger

logger = get_logger("TaskQueue")

class TaskSignals(QObject):
    finished = pyqtSignal(str)  # Task ID
    error = pyqtSignal(tuple)   # (Task ID, Exception string)
    result = pyqtSignal(object) # Can be anything
    progress = pyqtSignal(int)  # Percentage

class BrowserLaunchTask(QRunnable):
    def __init__(self, profile_id, profile_name, proxy_info=None, custom_url=None, external_path=None, automation_callback=None):
        super().__init__()
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.proxy_info = proxy_info
        self.custom_url = custom_url
        self.external_path = external_path
        self.automation_callback = automation_callback
        self.signals = TaskSignals()
        self.task_id = f"launch_{self.profile_name}"

    @pyqtSlot()
    def run(self):
        try:
            from src.modules.automation.browser import BrowserManager
            logger.info(f"Task started: Launching {self.profile_name}")

            browser_mgr = BrowserManager()
            driver = browser_mgr.launch_profile(self.profile_name, self.proxy_info, self.external_path)

            if driver:
                if self.custom_url:
                    try:
                        url = self.custom_url
                        if not url.startswith("http://") and not url.startswith("https://"):
                            url = "https://" + url
                        driver.get(url)
                    except Exception as e:
                        logger.error(f"Failed to load custom URL {self.custom_url}: {e}")

                self.signals.result.emit(driver)

                # Execute Selenium automation directly in this background thread
                if self.automation_callback:
                    try:
                        self.automation_callback(driver)
                    except Exception as ac_err:
                        logger.error(f"Automation callback failed for {self.profile_name}: {ac_err}")
                # Now wait for the driver to be manually closed
                import time
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
                self.signals.finished.emit(self.task_id)
            else:
                self.signals.error.emit((self.task_id, "Failed to launch driver (returned None)"))
        except Exception as e:
            logger.error(f"Error in BrowserLaunchTask: {e}")
            self.signals.error.emit((self.task_id, str(e)))

class TaskQueueManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskQueueManager, cls).__new__(cls)
            cls._instance.threadpool = QThreadPool()
            # Increase max thread count so holding threads open with the while loop
            # doesn't starve the pool and prevent other profiles from launching.
            cls._instance.threadpool.setMaxThreadCount(50)
            logger.info(f"Task Queue initialized. Max threads: {cls._instance.threadpool.maxThreadCount()}")
        return cls._instance

    def add_task(self, runnable_task):
        self.threadpool.start(runnable_task)
