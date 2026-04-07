from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QHeaderView, QLabel, QComboBox, QCheckBox, QLineEdit,
                             QTableWidgetItem, QInputDialog, QMessageBox, QDialog, QSplitter, QTextEdit, QMenu, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject, pyqtSignal
from src.modules.profiles.manager import ProfileManager
from src.modules.proxies.manager import ProxyManager
from src.modules.tasks.queue_manager import TaskQueueManager, BrowserLaunchTask
from src.utils.logger import get_logger, ui_log_handler

logger = get_logger("ProfilesView")

class TaskSignalBridge(QObject):
    # We need an intermediate QObject that lives in the main thread to receive signals
    # from QRunnables and dispatch them to the view
    status_update_signal = pyqtSignal(int, str) # profile_id, status

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.status_update_signal.connect(self.view.update_profile_status)

    @pyqtSlot(int, str)
    def update_status(self, profile_id, status):
        self.status_update_signal.emit(profile_id, status)


class ProfilesView(QWidget):
    def __init__(self):
        super().__init__()
        self.profile_manager = ProfileManager()
        self.proxy_manager = ProxyManager()
        self.task_queue = TaskQueueManager()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.signal_bridge = TaskSignalBridge(self)

        # Main splitter to hold top table and bottom logs
        splitter = QSplitter(Qt.Orientation.Vertical)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Top Toolbar
        toolbar = QHBoxLayout()

        self.group_combo = QComboBox()
        self.group_combo.setFixedWidth(150)
        self.group_combo.currentTextChanged.connect(self.load_profiles)

        self.scan_btn = QPushButton("Scan Profiles")
        self.scan_btn.clicked.connect(self.scan_profiles)
        self.cleanup_btn = QPushButton("Files Cleanup")
        self.cleanup_btn.setStyleSheet("background-color: #f38ba8; color: #11111b;")
        self.cleanup_btn.clicked.connect(self.cleanup_profiles)

        toolbar.addWidget(QLabel("Filter by Group:"))
        toolbar.addWidget(self.group_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.scan_btn)
        toolbar.addWidget(self.cleanup_btn)

        # Actions Toolbar (Split into two rows for better spacing)
        actions_layout = QVBoxLayout()
        actions_bar_1 = QHBoxLayout()
        actions_bar_2 = QHBoxLayout()

        self.btn_add = QPushButton("Create Bulk")
        self.btn_add.clicked.connect(self.create_bulk_profiles)
        self.btn_import = QPushButton("Import")
        self.btn_import.clicked.connect(self.import_profiles)
        self.btn_export = QPushButton("Export")
        self.btn_export.clicked.connect(self.export_profiles)
        self.btn_import_cookies = QPushButton("Import Cookies")
        self.btn_import_cookies.clicked.connect(self.import_cookies)
        self.btn_export_cookies = QPushButton("Export Cookies")
        self.btn_export_cookies.clicked.connect(self.export_cookies)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("background-color: #eba0ac; color: #11111b;")
        self.btn_delete.clicked.connect(self.delete_selected_profiles)
        self.btn_proxies = QPushButton("Manage Proxies")
        self.btn_proxies.clicked.connect(self.open_proxy_manager)

        actions_bar_1.addWidget(self.btn_add)
        actions_bar_1.addWidget(self.btn_import)
        actions_bar_1.addWidget(self.btn_export)
        actions_bar_1.addWidget(self.btn_import_cookies)
        actions_bar_1.addWidget(self.btn_export_cookies)
        actions_bar_1.addWidget(self.btn_delete)
        actions_bar_1.addWidget(self.btn_proxies)
        actions_bar_1.addStretch()

        # Start options
        self.start_btn = QPushButton("Start Selected")
        self.start_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b;")

        self.btn_auto_login = QPushButton("FB Auto Login")
        self.btn_auto_login.setStyleSheet("background-color: #89b4fa; color: #11111b;")
        self.btn_auto_login.clicked.connect(self.start_auto_login)

        self.one_by_one_cb = QCheckBox("One by One")
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("Custom URL on Open (Optional)")
        self.custom_url_input.setFixedWidth(200)
        self.start_btn.clicked.connect(self.start_selected_profiles)

        actions_bar_2.addStretch()
        actions_bar_2.addWidget(self.btn_auto_login)
        actions_bar_2.addWidget(self.custom_url_input)
        actions_bar_2.addWidget(self.one_by_one_cb)
        actions_bar_2.addWidget(self.start_btn)

        actions_layout.addLayout(actions_bar_1)
        actions_layout.addLayout(actions_bar_2)

        # Select All Checkbox (placed above table or in corner)
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        toolbar.insertWidget(0, self.select_all_cb)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["", "ID", "Profile Name", "Group", "Proxy", "Created", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 30)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        top_layout.addLayout(toolbar)
        top_layout.addLayout(actions_layout)
        top_layout.addWidget(self.table)

        # Log Console
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4; font-family: monospace;")
        ui_log_handler.log_signal.connect(self.append_log)

        splitter.addWidget(top_widget)
        splitter.addWidget(self.log_console)
        splitter.setSizes([600, 150]) # Give more space to table

        layout.addWidget(splitter)

        self.load_groups()
        self.load_profiles()

    def append_log(self, level, message):
        color = "#cdd6f4" # Default text color
        if level == "ERROR" or level == "CRITICAL":
            color = "#f38ba8" # Red
        elif level == "WARNING":
            color = "#f9e2af" # Yellow
        elif level == "INFO":
            color = "#a6e3a1" # Green

        formatted_msg = f"<span style='color: {color}'>{message}</span>"
        self.log_console.append(formatted_msg)

    def toggle_select_all(self, state):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 0)
            if item:
                # The checkbox is the first child of the layout inside the QWidget wrapper
                cb = item.layout().itemAt(0).widget()
                if isinstance(cb, QCheckBox):
                    cb.setChecked(state == Qt.CheckState.Checked.value)

    def get_selected_rows(self):
        selected_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 0)
            if item:
                cb = item.layout().itemAt(0).widget()
                if isinstance(cb, QCheckBox) and cb.isChecked():
                    selected_rows.append(row)
        return selected_rows

    @pyqtSlot(int, str)
    def update_profile_status(self, profile_id, status):
        # Update DB
        self.profile_manager.db.execute("UPDATE profiles SET status = ? WHERE id = ?", (status, profile_id))
        # Update UI Table
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 1).text()) == profile_id:
                self.table.item(row, 6).setText(status)
                break

    def load_groups(self):
        current = self.group_combo.currentText()
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self.group_combo.addItem("All Groups")
        groups = self.profile_manager.get_all_groups()
        self.group_combo.addItems(groups)

        if current in [self.group_combo.itemText(i) for i in range(self.group_combo.count())]:
            self.group_combo.setCurrentText(current)
        self.group_combo.blockSignals(False)

    def load_profiles(self):
        group = self.group_combo.currentText()
        if group == "All Groups" or not group:
            profiles = self.profile_manager.get_all_profiles()
        else:
            profiles = self.profile_manager.get_profiles_by_group(group)

        self.select_all_cb.blockSignals(True)
        self.select_all_cb.setChecked(False)
        self.select_all_cb.blockSignals(False)

        self.table.setRowCount(0)
        for row_idx, profile in enumerate(profiles):
            self.table.insertRow(row_idx)

            # Checkbox
            cb = QCheckBox()
            # Center the checkbox
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_idx, 0, cb_widget)

            # ID
            item_id = QTableWidgetItem(str(profile['id']))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 1, item_id)

            # Name
            item_name = QTableWidgetItem(profile['name'])
            item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 2, item_name)

            # Group
            item_group = QTableWidgetItem(profile['group_name'] or "Default")
            item_group.setFlags(item_group.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 3, item_group)

            # Proxy
            proxy_str = f"{profile['ip']}:{profile['port']}" if profile['ip'] and profile['port'] else "None"
            item_proxy = QTableWidgetItem(proxy_str)
            item_proxy.setFlags(item_proxy.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 4, item_proxy)

            # Created
            created_str = str(profile['created_at']).split('.')[0] if profile['created_at'] else ""
            item_created = QTableWidgetItem(created_str)
            item_created.setFlags(item_created.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 5, item_created)

            # Status
            item_status = QTableWidgetItem(profile['status'] or "Unknown")
            item_status.setFlags(item_status.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 6, item_status)

    def show_context_menu(self, position):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return

        menu = QMenu()
        assign_group_action = menu.addAction("Assign Group")
        assign_proxy_action = menu.addAction("Assign Proxy")

        action = menu.exec(self.table.viewport().mapToGlobal(position))

        if action == assign_group_action:
            group, ok = QInputDialog.getText(self, "Assign Group", "Enter new group name:")
            if ok and group:
                group_name = group.strip() if group.strip() else "Default"
                for row in selected_rows:
                    profile_id = int(self.table.item(row, 1).text())
                    self.profile_manager.db.execute("UPDATE profiles SET group_name = ? WHERE id = ?", (group_name, profile_id))
                self.load_groups()
                self.load_profiles()
                logger.info(f"Assigned group '{group_name}' to {len(selected_rows)} profiles.")

        elif action == assign_proxy_action:
            proxies = self.proxy_manager.get_all_proxies()
            proxy_list = ["None"] + [f"{p['id']} - {p['ip']}:{p['port']}" for p in proxies]

            proxy_sel, ok = QInputDialog.getItem(self, "Assign Proxy", "Select Proxy:", proxy_list, 0, False)
            if ok:
                proxy_id = None
                if proxy_sel != "None":
                    proxy_id = int(proxy_sel.split(" - ")[0])

                for row in selected_rows:
                    p_id = int(self.table.item(row, 1).text())
                    self.profile_manager.db.execute("UPDATE profiles SET proxy_id = ? WHERE id = ?", (proxy_id, p_id))

                self.load_profiles()
                logger.info(f"Assigned proxy {proxy_id} to {len(selected_rows)} profiles.")

    def create_bulk_profiles(self):
        prefix, ok = QInputDialog.getText(self, "Profile Prefix", "Enter prefix for profiles (e.g., fb_acc):")
        if ok and prefix:
            count, ok2 = QInputDialog.getInt(self, "Number of Profiles", "How many profiles to create?", 1, 1, 1000)
            if ok2:
                group, ok3 = QInputDialog.getText(self, "Group Name", "Enter group name (or leave empty for Default):")
                if ok3:
                    group_name = group.strip() if group.strip() else "Default"
                    self.profile_manager.bulk_create_profiles(prefix, count, group_name)
                    self.load_groups()
                    self.load_profiles()
                    QMessageBox.information(self, "Success", f"Successfully created {count} profiles.")

    def open_proxy_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Proxies")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)

        proxy_input = QLineEdit()
        proxy_input.setPlaceholderText("IP:PORT:USER:PASS or IP:PORT")
        add_btn = QPushButton("Add Proxy")
        import_btn = QPushButton("Import .txt")

        h_layout = QHBoxLayout()
        h_layout.addWidget(proxy_input)
        h_layout.addWidget(add_btn)
        h_layout.addWidget(import_btn)
        layout.addLayout(h_layout)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["ID", "IP", "Port", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        def load_proxies():
            proxies = self.proxy_manager.get_all_proxies()
            table.setRowCount(0)
            for r, p in enumerate(proxies):
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(str(p['id'])))
                table.setItem(r, 1, QTableWidgetItem(p['ip']))
                table.setItem(r, 2, QTableWidgetItem(p['port']))
                table.setItem(r, 3, QTableWidgetItem(p['status']))

        def add_proxy_handler():
            val = proxy_input.text().strip()
            parts = val.split(":")
            if len(parts) >= 2:
                self.proxy_manager.add_proxy(parts[0], parts[1], parts[2] if len(parts)>2 else None, parts[3] if len(parts)>3 else None)
                proxy_input.clear()
                load_proxies()

        def import_proxies_handler():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Proxy List", "", "Text Files (*.txt)")
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split(":")
                        if len(parts) >= 2:
                            self.proxy_manager.add_proxy(parts[0], parts[1], parts[2] if len(parts)>2 else None, parts[3] if len(parts)>3 else None)
                load_proxies()
                QMessageBox.information(dialog, "Success", "Proxies imported successfully.")

        add_btn.clicked.connect(add_proxy_handler)
        import_btn.clicked.connect(import_proxies_handler)
        load_proxies()

        dialog.exec()

    def scan_profiles(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan for Profiles")
        if not dir_path:
            return

        import os
        found_profiles = []
        try:
            for item in os.listdir(dir_path):
                if os.path.isdir(os.path.join(dir_path, item)):
                    found_profiles.append(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read directory: {e}")
            return

        if not found_profiles:
            QMessageBox.information(self, "Scan Complete", "No directories found in the selected folder.")
            return

        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QDialogButtonBox, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Profiles to Import")
        dialog.resize(400, 500)

        layout = QVBoxLayout(dialog)

        select_all_cb = QCheckBox("Select All")
        layout.addWidget(select_all_cb)

        list_widget = QListWidget()
        for profile in found_profiles:
            item = QListWidgetItem(profile)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            list_widget.addItem(item)

        def toggle_all(state):
            for i in range(list_widget.count()):
                list_widget.item(i).setCheckState(Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked)

        select_all_cb.stateChanged.connect(toggle_all)
        layout.addWidget(list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_to_add = []
            for i in range(list_widget.count()):
                if list_widget.item(i).checkState() == Qt.CheckState.Checked:
                    selected_to_add.append(list_widget.item(i).text())

            if not selected_to_add:
                return

            added = 0

            # Need to normalize paths to check if they are the same directory
            is_same_dir = os.path.normpath(dir_path) == os.path.normpath(self.profile_manager.profiles_dir)

            for profile_name in selected_to_add:
                # Add to database if not exists
                existing = self.profile_manager.db.fetchone("SELECT id FROM profiles WHERE name = ?", (profile_name,))
                if not existing:
                    external_path_to_save = None if is_same_dir else dir_path
                    self.profile_manager.create_profile(profile_name, "Imported", external_path=external_path_to_save)
                    added += 1

            QMessageBox.information(self, "Scan Complete", f"Successfully registered {added} profiles (Managed In-Place).")
            self.load_groups()
            self.load_profiles()

    def cleanup_profiles(self):
        reply = QMessageBox.question(self, "Cleanup Profiles", "This will delete all Cache and Temp files for all profiles.\nSessions/Cookies will be preserved.\n\nContinue?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Run in a background thread to avoid UI freeze
            import threading

            def run_cleanup():
                try:
                    cleaned, freed_bytes = self.profile_manager.cleanup_profile_files()
                    freed_mb = freed_bytes / (1024 * 1024)
                    # We need to use a signal or QTimer to safely show QMessageBox from main thread
                    # For simplicity, using a small QTimer delay injected back into the main loop
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: QMessageBox.information(self, "Cleanup Complete", f"Cleaned cache for {cleaned} profiles.\nFreed {freed_mb:.2f} MB of space."))
                except Exception as e:
                    logger.error(f"Cleanup failed: {e}")
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Cleanup encountered an error: {e}"))

            self.cleanup_btn.setEnabled(False)
            self.cleanup_btn.setText("Cleaning...")

            def on_finished():
                self.cleanup_btn.setEnabled(True)
                self.cleanup_btn.setText("Files Cleanup")

            thread = threading.Thread(target=run_cleanup)
            thread.start()

            # Simple polling to reset button
            def check_thread():
                if not thread.is_alive():
                    on_finished()
                else:
                    QTimer.singleShot(500, check_thread)
            QTimer.singleShot(500, check_thread)

    @pyqtSlot(int)
    def _on_import_success(self, count):
        if count > 0:
            QMessageBox.information(self, "Import Successful", f"Successfully imported {count} profiles from ZIP.")
            self.load_groups()
            self.load_profiles()
        else:
            QMessageBox.information(self, "Import Status", "No new profiles were found in the ZIP or they already exist.")
        self.btn_import.setEnabled(True)
        self.btn_import.setText("Import")

    @pyqtSlot(str)
    def _on_import_error(self, error_msg):
        QMessageBox.critical(self, "Import Error", f"Failed to import profiles: {error_msg}")
        self.btn_import.setEnabled(True)
        self.btn_import.setText("Import")

    def import_profiles(self):
        import os
        import zipfile
        import threading
        from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
        file_path, _ = QFileDialog.getOpenFileName(self, "Select ZIP Profile Backup to Import", "", "ZIP Files (*.zip)")
        if file_path:
            self.btn_import.setEnabled(False)
            self.btn_import.setText("Importing...")

            def run_import():
                try:
                    # The ZIP file is expected to contain the profile folders directly inside it
                    imported_count = 0
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        # Get list of top-level directories in the zip
                        top_level_dirs = set()
                        for name in zip_ref.namelist():
                            parts = name.split('/')
                            if parts[0]:
                                top_level_dirs.add(parts[0])

                        for profile_name in top_level_dirs:
                            target_path = os.path.join(self.profile_manager.profiles_dir, profile_name)
                            if not os.path.exists(target_path):
                                # Extract specific profile directory
                                members = [m for m in zip_ref.namelist() if m.startswith(profile_name + '/')]
                                zip_ref.extractall(path=self.profile_manager.profiles_dir, members=members)
                                self.profile_manager.create_profile(profile_name, "Imported")
                                imported_count += 1

                    QMetaObject.invokeMethod(self, "_on_import_success", Qt.ConnectionType.QueuedConnection, Q_ARG(int, imported_count))
                except Exception as e:
                    logger.error(f"Failed to import ZIP: {e}")
                    QMetaObject.invokeMethod(self, "_on_import_error", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

            threading.Thread(target=run_import, daemon=True).start()

    @pyqtSlot(int, str)
    def _on_export_success(self, count, file_path):
        QMessageBox.information(self, "Export Successful", f"Successfully exported {count} profiles to:\n{file_path}")
        self.btn_export.setEnabled(True)
        self.btn_export.setText("Export")

    @pyqtSlot(str)
    def _on_export_error(self, error_msg):
        QMessageBox.critical(self, "Export Error", f"Failed to export profiles: {error_msg}")
        self.btn_export.setEnabled(True)
        self.btn_export.setText("Export")

    def export_profiles(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to export.")
            return

        export_file, _ = QFileDialog.getSaveFileName(self, "Save Export as ZIP", "profiles_backup.zip", "ZIP Files (*.zip)")
        if not export_file:
            return

        import os
        import json
        import sqlite3
        import zipfile
        import base64
        import tempfile
        import threading
        from PyQt6.QtCore import QMetaObject, Q_ARG, Qt

        try:
            import win32crypt
        except ImportError:
            QMessageBox.warning(self, "Missing Dependency", "The 'pywin32' package is required for cross-device cookie export on Windows.")
            return

        self.btn_export.setEnabled(False)
        self.btn_export.setText("Exporting...")

        def run_export():
            try:
                exported_count = 0
                with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for row in selected_rows:
                        # Extracting text from QTableWidgetItem in background thread is generally okay since they are copies, but strictly we should pass the text values.
                        profile_name = self.table.item(row, 2).text()

                        # Get external_path directly from DB since it's not in the table view
                        profile_data = self.profile_manager.db.fetchone("SELECT external_path FROM profiles WHERE name = ?", (profile_name,))
                        external_path = profile_data['external_path'] if profile_data else None

                        if external_path:
                            source_path = os.path.join(external_path, profile_name)
                        else:
                            source_path = os.path.join(self.profile_manager.profiles_dir, profile_name)

                        if os.path.exists(source_path):
                            for root, dirs, files in os.walk(source_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    # Make arcname relative to profiles_dir so it preserves the profile folder name
                                    base_dir = external_path if external_path else self.profile_manager.profiles_dir
                                    arcname = os.path.relpath(file_path, base_dir)
                                    zipf.write(file_path, arcname)
                            exported_count += 1

                QMetaObject.invokeMethod(self, "_on_export_success", Qt.ConnectionType.QueuedConnection, Q_ARG(int, exported_count), Q_ARG(str, export_file))
            except Exception as e:
                logger.error(f"Failed to export ZIP: {e}")
                QMetaObject.invokeMethod(self, "_on_export_error", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=run_export, daemon=True).start()

    def format_netscape_cookies(self, cookies_list):
        lines = ["# Netscape HTTP Cookie File", "# https://curl.haxx.se/rfc/cookie_spec.html", "# This is a generated file!  Do not edit.", ""]
        for c in cookies_list:
            domain = c.get('domain', '')
            include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
            path = c.get('path', '/')
            secure = "TRUE" if c.get('secure') else "FALSE"
            expiry = str(int(c.get('expirationDate', 0))) if c.get('expirationDate') else "0"
            name = c.get('name', '')
            value = c.get('value', '')
            lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")
        return "\n".join(lines)

    def export_cookies(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to export cookies from.")
            return

        format_reply = QMessageBox.question(self, "Export Format", "Export as JSON?\n(Click 'No' to export as Netscape TXT)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if format_reply == QMessageBox.StandardButton.Cancel:
            return

        export_ext = ".json" if format_reply == QMessageBox.StandardButton.Yes else ".txt"

        reply = QMessageBox.question(self, "Export Method", "Do you want to save as a ZIP archive?\n(Click 'No' to select a folder and save files directly)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel:
            return

        export_mode = "ZIP" if reply == QMessageBox.StandardButton.Yes else "DIR"

        target_path = ""
        if export_mode == "ZIP":
            target_path, _ = QFileDialog.getSaveFileName(self, "Save Cookies as ZIP", f"cookies_backup.zip", "ZIP Files (*.zip)")
            if not target_path:
                return
        else:
            target_path = QFileDialog.getExistingDirectory(self, "Select Folder to Export Cookies")
            if not target_path:
                return

        import os
        import json
        import zipfile
        import sqlite3
        import base64
        import tempfile
        try:
            import win32crypt
        except ImportError:
            QMessageBox.warning(self, "Missing Dependency", "The 'pywin32' package is required for cross-device cookie export on Windows.")
            return

        exported_count = 0

        try:
            zipf = zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) if export_mode == "ZIP" else None

            for row in selected_rows:
                profile_name = self.table.item(row, 2).text()

                profile_data = self.profile_manager.db.fetchone("SELECT external_path FROM profiles WHERE name = ?", (profile_name,))
                external_path = profile_data['external_path'] if profile_data else None

                if external_path:
                    source_path = os.path.join(external_path, profile_name)
                else:
                    source_path = os.path.join(self.profile_manager.profiles_dir, profile_name)

                cookies_path = os.path.join(source_path, "Default", "Network", "Cookies")
                local_state_path = os.path.join(source_path, "Local State")

                if os.path.exists(cookies_path) and os.path.exists(local_state_path):
                    # Extract DPAPI key
                    try:
                        with open(local_state_path, "r", encoding="utf-8") as f:
                            local_state = json.load(f)
                        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                        encrypted_key = encrypted_key[5:] # Remove DPAPI prefix
                        decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

                        # Connect to SQLite DB
                        from Crypto.Cipher import AES

                        def decrypt_value(enc_value, key):
                            try:
                                iv = enc_value[3:15]
                                payload = enc_value[15:]
                                cipher = AES.new(key, AES.MODE_GCM, iv)
                                return cipher.decrypt(payload)[:-16].decode()
                            except Exception:
                                return ""

                        conn = sqlite3.connect(cookies_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT host_key, name, value, encrypted_value, path, expires_utc, is_secure, is_httponly FROM cookies")

                        cookies_list = []
                        for host_key, name, value, encrypted_value, path, expires_utc, is_secure, is_httponly in cursor.fetchall():
                            decrypted_val = value
                            if encrypted_value:
                                decrypted_val = decrypt_value(encrypted_value, decrypted_key)

                            cookies_list.append({
                                "domain": host_key,
                                "name": name,
                                "value": decrypted_val,
                                "path": path,
                                "expirationDate": expires_utc / 1000000 - 11644473600 if expires_utc else None,
                                "secure": bool(is_secure),
                                "httpOnly": bool(is_httponly)
                            })
                        conn.close()

                        if cookies_list:
                            file_content = json.dumps(cookies_list, indent=4) if export_ext == ".json" else self.format_netscape_cookies(cookies_list)
                            file_name = f"{profile_name}_cookies{export_ext}"

                            if export_mode == "ZIP":
                                zipf.writestr(file_name, file_content)
                            else:
                                with open(os.path.join(target_path, file_name), 'w', encoding='utf-8') as f:
                                    f.write(file_content)
                            exported_count += 1

                    except Exception as e:
                        logger.error(f"Error decrypting cookies for {profile_name}: {e}")

            if zipf:
                zipf.close()

            QMessageBox.information(self, "Export Successful", f"Successfully exported cookies for {exported_count} profiles to:\n{target_path}")
        except Exception as e:
            logger.error(f"Failed to export cookies: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export cookies: {e}")

    def parse_netscape_cookies(self, file_path):
        import time
        cookies = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) >= 7:
                        cookies.append({
                            "domain": parts[0],
                            "httpOnly": parts[0].startswith('#HttpOnly_'),
                            "path": parts[2],
                            "secure": parts[3].lower() == 'true',
                            "expirationDate": float(parts[4]) if parts[4].isdigit() and int(parts[4]) > 0 else time.time() + 31536000,
                            "name": parts[5],
                            "value": parts[6]
                        })
        except Exception as e:
            logger.error(f"Failed to parse netscape cookies from {file_path}: {e}")
        return cookies

    def import_cookies(self):
        import os
        import json
        import shutil

        reply = QMessageBox.question(self, "Import Cookies",
                                     "How do you want to import cookies?\n\nYes: Select individual files (.json, .txt)\nNo: Select a folder to bulk import",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Cancel:
            return

        files_to_process = []

        if reply == QMessageBox.StandardButton.Yes:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Cookie Files", "", "Cookie Files (*.json *.txt)")
            if not file_paths:
                return
            files_to_process = file_paths
        else:
            dir_path = QFileDialog.getExistingDirectory(self, "Select Folder with Cookie Files")
            if not dir_path:
                return
            for f in os.listdir(dir_path):
                if f.endswith('.json') or f.endswith('.txt'):
                    files_to_process.append(os.path.join(dir_path, f))

        if not files_to_process:
            QMessageBox.information(self, "Import Status", "No valid cookie files found.")
            return

        imported_count = 0
        try:
            for file_path in files_to_process:
                filename = os.path.basename(file_path)
                profile_name, ext = os.path.splitext(filename)

                # Check if it's named with _cookies suffix from our own export, if so, strip it
                if profile_name.endswith("_cookies"):
                    profile_name = profile_name[:-8]

                target_path = os.path.join(self.profile_manager.profiles_dir, profile_name)

                # Create profile if it doesn't exist
                existing = self.profile_manager.db.fetchone("SELECT id FROM profiles WHERE name = ?", (profile_name,))
                if not existing:
                    os.makedirs(target_path, exist_ok=True)
                    self.profile_manager.create_profile(profile_name, "Imported")

                extract_path = os.path.join(target_path, "import_cookies.json")

                if ext.lower() == '.json':
                    shutil.copy(file_path, extract_path)
                    imported_count += 1
                elif ext.lower() == '.txt':
                    parsed = self.parse_netscape_cookies(file_path)
                    if parsed:
                        with open(extract_path, 'w', encoding='utf-8') as f:
                            json.dump(parsed, f, indent=4)
                        imported_count += 1

            if imported_count > 0:
                self.load_groups()
                self.load_profiles()
                QMessageBox.information(self, "Import Successful", f"Successfully imported cookies for {imported_count} profiles.\nThey will be injected on next launch.")
            else:
                QMessageBox.warning(self, "Import Status", "Failed to parse any cookies from the selected files.")

        except Exception as e:
            logger.error(f"Failed to import cookies: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import cookies: {e}")

    def delete_selected_profiles(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete {len(selected_rows)} selected profile(s)?\nThis will also delete the profile folders.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                profile_id = int(self.table.item(row, 1).text())
                self.profile_manager.delete_profile(profile_id, delete_files=True)
            self.load_groups()
            self.load_profiles()

    def start_auto_login(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to auto-login.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Credentials File", "", "Text Files (*.txt)")
        if not file_path:
            return

        try:
            credentials = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        credentials.append((parts[0].strip(), parts[1].strip()))

            if not credentials:
                QMessageBox.warning(self, "File Error", "No valid credentials found. Format should be: username,password per line.")
                return

            if len(credentials) < len(selected_rows):
                QMessageBox.warning(self, "Mismatch", f"Found {len(credentials)} credentials but {len(selected_rows)} profiles selected.\nOnly the first {len(credentials)} profiles will be logged in.")

            # Prompt for thread count according to instructions: "user se poch ly kitni threads mai krna hai"
            threads_count, ok = QInputDialog.getInt(self, "Thread Count", "How many profiles to run concurrently?\n(Select 1 for one-by-one)", 1, 1, 50)
            if not ok:
                return

            self.task_queue.threadpool.setMaxThreadCount(threads_count)

            import time
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            for i, row in enumerate(selected_rows):
                if i >= len(credentials):
                    break

                profile_name = self.table.item(row, 2).text()
                profile_id = int(self.table.item(row, 1).text())
                username, password = credentials[i]

                profile_data = self.profile_manager.get_profile_by_id(profile_id)
                proxy_info = None
                if profile_data and profile_data['proxy_id']:
                    proxy_info = self.proxy_manager.get_proxy_by_id(profile_data['proxy_id'])

                # We pass the automation_callback directly to the task so it runs in the background thread.
                def inject_login(driver, u=username, p=password, p_name=profile_name):
                    try:
                        logger.info(f"Starting auto-login for {p_name} ({u})")
                        wait = WebDriverWait(driver, 15)

                        # Handle cookie consent if it appears (common in EU/UK IPs)
                        try:
                            cookie_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Allow all cookies' or @title='Decline optional cookies']")))
                            cookie_btn.click()
                            time.sleep(1)
                        except:
                            pass

                        # Wait for email field
                        email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
                        email_field.clear()
                        email_field.send_keys(u)

                        # Wait for password field
                        pass_field = wait.until(EC.presence_of_element_located((By.ID, "pass")))
                        pass_field.clear()
                        pass_field.send_keys(p)

                        # Find and click login button (name='login')
                        login_btn = wait.until(EC.element_to_be_clickable((By.NAME, "login")))
                        time.sleep(1) # Humanize slightly
                        login_btn.click()

                        logger.info(f"Auto-login submitted for {p_name}")
                    except Exception as e:
                        logger.error(f"Auto-login failed for {p_name}: {e}")

                ext_path = profile_data['external_path'] if profile_data and 'external_path' in profile_data.keys() else None
                task = BrowserLaunchTask(profile_id, profile_name, proxy_info, custom_url="https://www.facebook.com/", external_path=ext_path, automation_callback=inject_login)

                def make_running_callback(pid=profile_id):
                    return lambda driver: self.signal_bridge.update_status(pid, "Running")
                def make_finished_callback(pid=profile_id):
                    return lambda t_id: self.signal_bridge.update_status(pid, "Ready")
                def make_error_callback(pid=profile_id):
                    return lambda err: self.signal_bridge.update_status(pid, "Failed")

                task.signals.result.connect(make_running_callback(profile_id))
                task.signals.finished.connect(make_finished_callback(profile_id))
                task.signals.error.connect(make_error_callback(profile_id))

                self.task_queue.add_task(task)
                self.signal_bridge.update_status(profile_id, "Pending")

            logger.info(f"Queued auto-login tasks with {threads_count} max threads.")

        except Exception as e:
            logger.error(f"Error reading credentials file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")

    def start_selected_profiles(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to start.")
            return

        # Determine concurrency
        if self.one_by_one_cb.isChecked():
            self.task_queue.threadpool.setMaxThreadCount(1)
        else:
            # Let's prompt for thread count if they are launching many and not using one-by-one checkbox
            if len(selected_rows) > 3:
                threads_count, ok = QInputDialog.getInt(self, "Thread Count", "How many profiles to launch concurrently?", 5, 1, 50)
                if not ok:
                    return
                self.task_queue.threadpool.setMaxThreadCount(threads_count)
            else:
                self.task_queue.threadpool.setMaxThreadCount(50)

        custom_url = self.custom_url_input.text().strip()

        for row in selected_rows:
            profile_name = self.table.item(row, 2).text()
            profile_id = int(self.table.item(row, 1).text())

            # Get full profile data to get proxy
            profile_data = self.profile_manager.get_profile_by_id(profile_id)
            proxy_info = None
            if profile_data and profile_data['proxy_id']:
                proxy_info = self.proxy_manager.get_proxy_by_id(profile_data['proxy_id'])

            ext_path = profile_data['external_path'] if profile_data and 'external_path' in profile_data.keys() else None
            task = BrowserLaunchTask(profile_id, profile_name, proxy_info, custom_url, external_path=ext_path)

            # Connect task signals to the UI bridge to prevent cross-thread UI updates
            def make_running_callback(pid=profile_id):
                return lambda driver: self.signal_bridge.update_status(pid, "Running")

            def make_finished_callback(pid=profile_id):
                return lambda t_id: self.signal_bridge.update_status(pid, "Ready")

            def make_error_callback(pid=profile_id):
                return lambda err: self.signal_bridge.update_status(pid, "Failed")

            task.signals.result.connect(lambda driver: logger.info(f"Browser launched for profile {profile_id}"))
            task.signals.finished.connect(lambda t_id: logger.info(f"Launch task finished: {t_id}"))
            task.signals.error.connect(lambda err: logger.error(f"Launch task error: {err[1]}"))

            task.signals.result.connect(make_running_callback(profile_id))
            task.signals.finished.connect(make_finished_callback(profile_id))
            task.signals.error.connect(make_error_callback(profile_id))

            self.task_queue.add_task(task)
            self.signal_bridge.update_status(profile_id, "Pending")
            logger.info(f"Queued start for profile: {profile_name}")
