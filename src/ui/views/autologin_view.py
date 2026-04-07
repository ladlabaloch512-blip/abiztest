from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSpinBox
from PyQt6.QtCore import Qt

class AutoLoginView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Auto FB Login")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select TXT file (user,pass per line)...")
        self.file_btn = QPushButton("Browse")
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.file_btn)

        thread_layout = QHBoxLayout()
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 20)
        self.threads_spin.setValue(3)
        thread_layout.addWidget(QLabel("Concurrent Threads:"))
        thread_layout.addWidget(self.threads_spin)
        thread_layout.addStretch()

        self.start_btn = QPushButton("Start Auto Login")
        self.start_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-size: 14px;")

        layout.addLayout(file_layout)
        layout.addLayout(thread_layout)
        layout.addSpacing(20)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
