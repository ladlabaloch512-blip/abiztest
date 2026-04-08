import sys
import os
import json
from datetime import datetime, timedelta

# Add parent dir to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from src.core.security import SecurityManager

class KeyGenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Key Generator")
        self.resize(400, 250)
        self.security = SecurityManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        title = QLabel("License Key Generator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")

        self.form_layout = QFormLayout()

        self.hwid_input = QLineEdit()
        self.hwid_input.setPlaceholderText("Enter User's HWID...")

        self.expiry_input = QLineEdit()
        # Default expiry: 30 days from now
        default_expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        self.expiry_input.setText(default_expiry)

        self.form_layout.addRow("Target HWID:", self.hwid_input)
        self.form_layout.addRow("Expiry Date:", self.expiry_input)

        self.generate_btn = QPushButton("Generate License")
        self.generate_btn.setStyleSheet("background-color: #25D366; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.generate_btn.clicked.connect(self._generate)

        self.layout.addWidget(title)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.generate_btn)

    def _generate(self):
        hwid = self.hwid_input.text().strip()
        expiry_str = self.expiry_input.text().strip()

        if not hwid:
            QMessageBox.warning(self, "Error", "HWID is required.")
            return

        try:
            # Validate date format
            datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid Date Format.\nUse: YYYY-MM-DD HH:MM:SS")
            return

        payload = {
            "hwid": hwid,
            "expiry_date": expiry_str
        }

        json_payload = json.dumps(payload)
        encrypted_payload = self.security.encrypt(json_payload)

        if not encrypted_payload:
            QMessageBox.critical(self, "Error", "Encryption failed.")
            return

        save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'license.lic'))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_payload)
            QMessageBox.information(self, "Success", f"License generated successfully!\nSaved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; }
        QLineEdit { background-color: #313244; border: 1px solid #45475a; padding: 5px; color: #cdd6f4; }
        QMessageBox { background-color: #1e1e2e; }
        QMessageBox QLabel { color: #cdd6f4; }
        QMessageBox QPushButton { background-color: #89b4fa; color: #11111b; min-width: 80px; padding: 5px; }
    """)
    window = KeyGenApp()
    window.show()
    sys.exit(app.exec())
