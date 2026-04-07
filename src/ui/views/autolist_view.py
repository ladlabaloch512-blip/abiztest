from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox, QLabel)

class AutoListView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Marketplace Auto-Listing Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.price_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Electronics", "Vehicles", "Property", "Apparel"])
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["New", "Used - Like New", "Used - Good", "Used - Fair"])
        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(100)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Or select a location TXT file...")
        loc_btn = QPushButton("Browse")
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(self.location_input)
        loc_layout.addWidget(loc_btn)

        self.images_btn = QPushButton("Select Images (Max 10)")

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 20)
        self.threads_spin.setValue(3)

        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Price:", self.price_input)
        form_layout.addRow("Category:", self.category_combo)
        form_layout.addRow("Condition:", self.condition_combo)
        form_layout.addRow("Description:", self.desc_input)
        form_layout.addRow("Location:", loc_layout)
        form_layout.addRow("Images:", self.images_btn)
        form_layout.addRow("Threads (Concurrent):", self.threads_spin)

        layout.addLayout(form_layout)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_save_template = QPushButton("Save as Template")
        btn_load_template = QPushButton("Load Template")
        btn_start = QPushButton("Start Auto Listing")
        btn_start.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-size: 14px;")

        btn_layout.addWidget(btn_save_template)
        btn_layout.addWidget(btn_load_template)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_start)

        layout.addLayout(btn_layout)
        layout.addStretch()
