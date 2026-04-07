import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # Industrial Level Dark Theme Stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            color: #cdd6f4;
        }
        QLineEdit, QComboBox, QSpinBox, QTextEdit {
            background-color: #313244;
            border: 1px solid #45475a;
            padding: 8px;
            border-radius: 4px;
            color: #cdd6f4;
            selection-background-color: #89b4fa;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
            border: 1px solid #89b4fa;
        }
        QPushButton {
            background-color: #89b4fa;
            color: #11111b;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #b4befe;
        }
        QPushButton:pressed {
            background-color: #74c7ec;
        }
        /* Custom styled table */
        QTableWidget {
            background-color: #181825;
            color: #cdd6f4;
            gridline-color: #313244;
            border: 1px solid #313244;
            border-radius: 4px;
            selection-background-color: #45475a;
        }
        QHeaderView::section {
            background-color: #11111b;
            color: #a6adc8;
            padding: 6px;
            border: none;
            font-weight: bold;
            border-bottom: 1px solid #313244;
            border-right: 1px solid #313244;
        }
        QScrollBar:vertical {
            border: none;
            background: #181825;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #45475a;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #585b70;
        }
        QScrollBar:horizontal {
            border: none;
            background: #181825;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #45475a;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #585b70;
        }
        QMessageBox {
            background-color: #1e1e2e;
        }
        QMessageBox QLabel {
            color: #cdd6f4;
        }
        QMessageBox QPushButton {
            background-color: #89b4fa;
            color: #11111b;
            min-width: 80px;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
