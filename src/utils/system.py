import psutil
from src.utils.logger import get_logger

logger = get_logger("SystemUtils")

def get_system_resources():
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram_info = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_usage,
            "ram_percent": ram_info.percent,
            "ram_used_gb": round(ram_info.used / (1024**3), 2),
            "ram_total_gb": round(ram_info.total / (1024**3), 2)
        }
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        return {}

def kill_related_processes(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        logger.info(f"Killed process {pid} and its children.")
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
