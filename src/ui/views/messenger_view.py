from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit

class MessengerView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Combined Messenger & Discord")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        desc = QLabel("Fetch new messages from all profiles and sync them with Discord.")
        desc.setStyleSheet("color: #a6adc8; margin-bottom: 20px;")
        layout.addWidget(desc)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Sync logs will appear here...")

        btn_layout = QHBoxLayout()
        self.start_sync_btn = QPushButton("Start Sync Service")
        self.start_sync_btn.setStyleSheet("background-color: #89b4fa; color: #11111b;")

        self.stop_sync_btn = QPushButton("Stop Service")
        self.stop_sync_btn.setStyleSheet("background-color: #eba0ac; color: #11111b;")

        btn_layout.addWidget(self.start_sync_btn)
        btn_layout.addWidget(self.stop_sync_btn)
        btn_layout.addStretch()

        layout.addWidget(self.log_area)
        layout.addLayout(btn_layout)
