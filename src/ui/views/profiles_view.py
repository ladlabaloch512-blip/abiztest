from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QHeaderView, QLabel, QComboBox, QCheckBox, QLineEdit)
from PyQt6.QtCore import Qt

class ProfilesView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Top Toolbar
        toolbar = QHBoxLayout()

        self.group_combo = QComboBox()
        self.group_combo.addItems(["All Groups", "Group 1", "Group 2"])
        self.group_combo.setFixedWidth(150)

        self.scan_btn = QPushButton("Scan Profiles")
        self.cleanup_btn = QPushButton("Files Cleanup")
        self.cleanup_btn.setStyleSheet("background-color: #f38ba8; color: #11111b;")

        toolbar.addWidget(QLabel("Filter by Group:"))
        toolbar.addWidget(self.group_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.scan_btn)
        toolbar.addWidget(self.cleanup_btn)

        # Actions Toolbar
        actions_bar = QHBoxLayout()
        btn_add = QPushButton("Create Bulk")
        btn_import = QPushButton("Import")
        btn_export = QPushButton("Export")
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet("background-color: #eba0ac; color: #11111b;")

        # Start options
        self.start_btn = QPushButton("Start Selected")
        self.start_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b;")
        self.one_by_one_cb = QCheckBox("One by One")
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("Custom URL on Open (Optional)")
        self.custom_url_input.setFixedWidth(200)

        actions_bar.addWidget(btn_add)
        actions_bar.addWidget(btn_import)
        actions_bar.addWidget(btn_export)
        actions_bar.addWidget(btn_delete)
        actions_bar.addStretch()
        actions_bar.addWidget(self.custom_url_input)
        actions_bar.addWidget(self.one_by_one_cb)
        actions_bar.addWidget(self.start_btn)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Select", "Profile Name", "Group", "Proxy", "Created", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        layout.addLayout(toolbar)
        layout.addLayout(actions_bar)
        layout.addWidget(self.table)
