import threading
import queue
import time
from src.utils.logger import get_logger

logger = get_logger("TaskManager")

class Task:
    def __init__(self, task_id, name, target_func, *args, **kwargs):
        self.task_id = task_id
        self.name = name
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.status = "Pending" # Pending, Running, Completed, Failed, Paused
        self.result = None

    def execute(self):
        self.status = "Running"
        try:
            self.result = self.target_func(*self.args, **self.kwargs)
            self.status = "Completed"
        except Exception as e:
            logger.error(f"Task '{self.name}' failed: {e}")
            self.status = "Failed"
            self.result = str(e)

class TaskManager:
    def __init__(self, max_workers=5):
        self.task_queue = queue.Queue()
        self.tasks = {}
        self.max_workers = max_workers
        self.workers = []
        self._stop_event = threading.Event()
        self._start_workers()

    def _start_workers(self):
        for i in range(self.max_workers):
            t = threading.Thread(target=self._worker_loop, name=f"Worker-{i}")
            t.daemon = True
            t.start()
            self.workers.append(t)

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                task_id = self.task_queue.get(timeout=1)
                task = self.tasks.get(task_id)
                if task and task.status == "Pending":
                    logger.info(f"Starting task: {task.name}")
                    task.execute()
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker encountered an error: {e}")

    def add_task(self, name, target_func, *args, **kwargs):
        task_id = str(time.time())
        task = Task(task_id, name, target_func, *args, **kwargs)
        self.tasks[task_id] = task
        self.task_queue.put(task_id)
        return task_id

    def get_task_status(self, task_id):
        task = self.tasks.get(task_id)
        return task.status if task else "Unknown"

    def shutdown(self):
        self._stop_event.set()
        for t in self.workers:
            t.join(timeout=2)
