import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
                             QFormLayout, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.core.licensing import LicenseManager
from src.utils.system import get_system_resources
from src.utils.logger import get_logger

logger = get_logger("UI_MainWindow")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FB Marketplace Manager Pro")
        self.resize(1100, 750)
        self.license_manager = LicenseManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self._init_license_screen()
        self._init_main_app_screen()

        self._check_license_on_startup()

    def _init_license_screen(self):
        self.license_widget = QWidget()
        layout = QVBoxLayout(self.license_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Software Locked")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hwid_label = QLabel(f"Your HWID: {self.license_manager.get_hwid()}")
        hwid_label.setFont(QFont("Arial", 14))
        hwid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hwid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.copy_btn = QPushButton("Copy HWID")
        self.copy_btn.setFixedSize(150, 40)
        self.copy_btn.setStyleSheet("background-color: #313244; color: white; font-weight: bold; border-radius: 5px;")
        self.copy_btn.clicked.connect(self._copy_hwid)

        self.buy_btn = QPushButton("Buy Now")
        self.buy_btn.setFixedSize(150, 40)
        self.buy_btn.setStyleSheet("background-color: #25D366; color: white; font-weight: bold; border-radius: 5px;")
        self.buy_btn.clicked.connect(self._open_buy_link)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(20)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.buy_btn)

        layout.addWidget(title)
        layout.addWidget(hwid_label)
        layout.addLayout(btn_layout)

        self.stack.addWidget(self.license_widget)

    def _init_main_app_screen(self):
        self.app_widget = QWidget()
        layout = QVBoxLayout(self.app_widget)

        # Header (System Monitor)
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        self.sys_monitor_label = QLabel("CPU: 0% | RAM: 0%")
        self.sys_monitor_label.setFont(QFont("Arial", 10))

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.sys_monitor_label)

        # Tabs
        self.tabs = QTabWidget()
        self._init_profiles_tab()
        self._init_automation_tab()
        self._init_settings_tab()

        layout.addLayout(header_layout)
        layout.addWidget(self.tabs)

        self.stack.addWidget(self.app_widget)

        # Start System Monitor Timer
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_sys_monitor)
        self.sys_timer.start(2000)

    def _init_profiles_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Actions Layout
        actions_layout = QHBoxLayout()
        btn_add = QPushButton("Create Bulk Profiles")
        btn_import = QPushButton("Import Cookies/Profiles")
        btn_export = QPushButton("Export Selected")
        btn_delete = QPushButton("Delete Selected")
        btn_start = QPushButton("Start Selected")

        actions_layout.addWidget(btn_add)
        actions_layout.addWidget(btn_import)
        actions_layout.addWidget(btn_export)
        actions_layout.addWidget(btn_delete)
        actions_layout.addWidget(btn_start)

        # Profiles Table
        self.profiles_table = QTableWidget(0, 5)
        self.profiles_table.setHorizontalHeaderLabels(["Select", "Name", "Group", "Proxy", "Status"])
        self.profiles_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addLayout(actions_layout)
        layout.addWidget(self.profiles_table)
        self.tabs.addTab(tab, "Profiles & Proxies")

    def _init_automation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form_layout = QFormLayout()
        self.task_type = QLineEdit()
        self.task_type.setPlaceholderText("e.g. Auto Listing, Messenger Sync")
        form_layout.addRow("Select Task:", self.task_type)

        btn_run = QPushButton("Queue Task")

        # Task Queue Table
        self.tasks_table = QTableWidget(0, 4)
        self.tasks_table.setHorizontalHeaderLabels(["Task ID", "Type", "Target Profile", "Status"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addLayout(form_layout)
        layout.addWidget(btn_run)
        layout.addWidget(QLabel("Task Queue:"))
        layout.addWidget(self.tasks_table)

        self.tabs.addTab(tab, "Automation Tasks")

    def _init_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QFormLayout()

        # Discord Settings
        self.discord_token = QLineEdit()
        self.discord_channel = QLineEdit()
        form.addRow(QLabel("<b>Discord Settings</b>"))
        form.addRow("Bot Token:", self.discord_token)
        form.addRow("Channel ID:", self.discord_channel)

        # Cloud Sync Settings
        self.client_secret = QLineEdit()
        self.client_secret.setPlaceholderText("Path to Google Client Secret JSON")
        form.addRow(QLabel("<b>Cloud Sync Settings</b>"))
        form.addRow("Client Secret:", self.client_secret)

        btn_auth_drive = QPushButton("Authenticate Google Drive")
        btn_save = QPushButton("Save Settings")

        layout.addLayout(form)
        layout.addWidget(btn_auth_drive)
        layout.addWidget(btn_save)
        layout.addStretch()

        self.tabs.addTab(tab, "Settings & Integrations")

    def _copy_hwid(self):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(self.license_manager.get_hwid())
        QMessageBox.information(self, "Copied", "HWID copied to clipboard.")

    def _open_buy_link(self):
        import webbrowser
        buy_link = self.license_manager.config.get("buy_link", "https://wa.me/1234567890")
        hwid = self.license_manager.get_hwid()
        full_link = f"{buy_link}?text=Hi,%20I%20want%20to%20buy%20the%20software.%20My%20HWID%20is:%20{hwid}"
        webbrowser.open(full_link)

    def _check_license_on_startup(self):
        is_valid, message = self.license_manager.check_license()
        if is_valid:
            logger.info(message)
            self.stack.setCurrentWidget(self.app_widget)
        else:
            logger.warning(message)
            self.stack.setCurrentWidget(self.license_widget)

    def _update_sys_monitor(self):
        stats = get_system_resources()
        if stats:
            cpu = stats.get('cpu_percent', 0)
            ram = stats.get('ram_percent', 0)
            self.sys_monitor_label.setText(f"CPU: {cpu}% | RAM: {ram}%")
