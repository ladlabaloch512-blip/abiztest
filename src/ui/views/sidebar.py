from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

class SidebarMenu(QWidget):
    menu_selected = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                color: #a6adc8;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton:checked {
                background-color: #89b4fa;
                color: #11111b;
            }
            QLabel {
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)

        # Logo/Title
        title = QLabel("FB Manager Pro")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #89b4fa; padding-bottom: 20px;")
        layout.addWidget(title)

        self.buttons = []
        menus = ["Profiles & Proxies", "Auto Login", "Marketplace Auto-List", "Messenger & Discord", "Settings & Cloud Sync"]

        for idx, text in enumerate(menus):
            btn = QPushButton(text)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx: self._on_btn_clicked(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

    def _on_btn_clicked(self, index):
        for idx, btn in enumerate(self.buttons):
            btn.setChecked(idx == index)
        self.menu_selected.emit(index)
