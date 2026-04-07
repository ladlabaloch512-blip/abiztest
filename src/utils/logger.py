import logging
import os
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class SignaledLogHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(str, str) # level, message

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_signal.emit(record.levelname, msg)
        except RuntimeError:
            # Ignore "wrapped C/C++ object of type SignaledLogHandler has been deleted"
            # which happens during application shutdown when background threads (like undetected_chromedriver) log.
            pass

ui_log_handler = SignaledLogHandler()

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
