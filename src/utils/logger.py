import logging
import os
from datetime import datetime
import eel

class EelLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            # Call a JS function to append the log if eel is running
            try:
                eel.append_log(record.levelname, msg)()
            except Exception:
                pass
        except Exception:
            pass

ui_log_handler = EelLogHandler()

# Setup logging
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='a', encoding='utf-8'),
        logging.StreamHandler(),
        ui_log_handler
    ]
)

def get_logger(name):
    return logging.getLogger(name)
