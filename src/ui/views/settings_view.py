from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QPushButton, QLineEdit, QLabel

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Settings & Integrations")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        form = QFormLayout()

        self.discord_token = QLineEdit()
        self.discord_channel = QLineEdit()
        form.addRow(QLabel("<b>Discord Settings</b>"))
        form.addRow("Bot Token:", self.discord_token)
        form.addRow("Channel ID:", self.discord_channel)

        form.addRow(QLabel("")) # Spacer

        self.client_secret = QLineEdit()
        self.client_secret.setPlaceholderText("Path to client_secret.json")
        form.addRow(QLabel("<b>Google Drive Sync</b>"))
        form.addRow("OAuth Secret:", self.client_secret)

        layout.addLayout(form)

        auth_btn = QPushButton("Authenticate Google Drive")
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b;")

        layout.addWidget(auth_btn)
        layout.addWidget(save_btn)
        layout.addStretch()
