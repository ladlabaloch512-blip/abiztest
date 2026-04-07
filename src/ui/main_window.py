import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.core.licensing import LicenseManager
from src.utils.system import get_system_resources
from src.utils.logger import get_logger

from src.ui.views.sidebar import SidebarMenu
from src.ui.views.profiles_view import ProfilesView
from src.ui.views.autolist_view import AutoListView
from src.ui.views.autologin_view import AutoLoginView
from src.ui.views.messenger_view import MessengerView
from src.ui.views.settings_view import SettingsView

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
        app_layout = QHBoxLayout(self.app_widget)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarMenu()
        self.sidebar.menu_selected.connect(self._switch_view)

        # Main Content Area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Top Header (System Monitor)
        header_layout = QHBoxLayout()
        self.view_title = QLabel("Profiles & Proxies")
        self.view_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.view_title.setStyleSheet("color: #cdd6f4;")

        self.sys_monitor_label = QLabel("CPU: 0% | RAM: 0%")
        self.sys_monitor_label.setFont(QFont("Arial", 10))
        self.sys_monitor_label.setStyleSheet("color: #a6adc8; background-color: #313244; padding: 5px 10px; border-radius: 5px;")

        header_layout.addWidget(self.view_title)
        header_layout.addStretch()
        header_layout.addWidget(self.sys_monitor_label)

        # Views Stack
        self.views_stack = QStackedWidget()
        self.views_stack.addWidget(ProfilesView())
        self.views_stack.addWidget(AutoLoginView())
        self.views_stack.addWidget(AutoListView())
        self.views_stack.addWidget(MessengerView())
        self.views_stack.addWidget(SettingsView())

        content_layout.addLayout(header_layout)
        content_layout.addSpacing(10)
        content_layout.addWidget(self.views_stack)

        app_layout.addWidget(self.sidebar)
        app_layout.addWidget(self.content_area)

        self.stack.addWidget(self.app_widget)

        # Start System Monitor Timer
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_sys_monitor)
        self.sys_timer.start(2000)

    def _switch_view(self, index):
        self.views_stack.setCurrentIndex(index)
        titles = ["Profiles & Proxies", "Auto Login", "Marketplace Auto-List", "Messenger & Discord", "Settings & Cloud Sync"]
        self.view_title.setText(titles[index])

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
