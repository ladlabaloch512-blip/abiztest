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

        # Actions Toolbar
        actions_bar = QHBoxLayout()
        self.btn_add = QPushButton("Create Bulk")
        self.btn_add.clicked.connect(self.create_bulk_profiles)
        self.btn_import = QPushButton("Import")
        self.btn_import.clicked.connect(self.import_profiles)
        self.btn_export = QPushButton("Export")
        self.btn_export.clicked.connect(self.export_profiles)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("background-color: #eba0ac; color: #11111b;")
        self.btn_delete.clicked.connect(self.delete_selected_profiles)
        self.btn_proxies = QPushButton("Manage Proxies")
        self.btn_proxies.clicked.connect(self.open_proxy_manager)

        # Start options
        self.start_btn = QPushButton("Start Selected")
        self.start_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b;")
        self.one_by_one_cb = QCheckBox("One by One")
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("Custom URL on Open (Optional)")
        self.custom_url_input.setFixedWidth(200)
        self.start_btn.clicked.connect(self.start_selected_profiles)

        actions_bar.addWidget(self.btn_add)
        actions_bar.addWidget(self.btn_import)
        actions_bar.addWidget(self.btn_export)
        actions_bar.addWidget(self.btn_delete)
        actions_bar.addWidget(self.btn_proxies)
        actions_bar.addStretch()
        actions_bar.addWidget(self.custom_url_input)
        actions_bar.addWidget(self.one_by_one_cb)
        actions_bar.addWidget(self.start_btn)

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
        top_layout.addLayout(actions_bar)
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
        added = self.profile_manager.scan_profiles()
        if added > 0:
            QMessageBox.information(self, "Scan Complete", f"Found and added {added} orphaned profiles.")
            self.load_groups()
            self.load_profiles()
        else:
            QMessageBox.information(self, "Scan Complete", "No missing profiles found in the directory.")

    def cleanup_profiles(self):
        reply = QMessageBox.question(self, "Cleanup Profiles", "This will delete all Cache and Temp files for all profiles.\nSessions/Cookies will be preserved.\n\nContinue?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cleaned, freed_bytes = self.profile_manager.cleanup_profile_files()
            freed_mb = freed_bytes / (1024 * 1024)
            QMessageBox.information(self, "Cleanup Complete", f"Cleaned cache for {cleaned} profiles.\nFreed {freed_mb:.2f} MB of space.")

    def import_profiles(self):
        import os
        import zipfile
        file_path, _ = QFileDialog.getOpenFileName(self, "Select ZIP Profile Backup to Import", "", "ZIP Files (*.zip)")
        if file_path:
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

                if imported_count > 0:
                    QMessageBox.information(self, "Import Successful", f"Successfully imported {imported_count} profiles from ZIP.")
                    self.load_groups()
                    self.load_profiles()
                else:
                    QMessageBox.information(self, "Import Status", "No new profiles were found in the ZIP or they already exist.")
            except Exception as e:
                logger.error(f"Failed to import ZIP: {e}")
                QMessageBox.critical(self, "Import Error", f"Failed to import profiles: {e}")

    def export_profiles(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to export.")
            return

        export_file, _ = QFileDialog.getSaveFileName(self, "Save Export as ZIP", "profiles_backup.zip", "ZIP Files (*.zip)")
        if not export_file:
            return

        import os
        import zipfile
        exported_count = 0

        try:
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for row in selected_rows:
                    profile_name = self.table.item(row, 2).text()
                    source_path = os.path.join(self.profile_manager.profiles_dir, profile_name)

                    if os.path.exists(source_path):
                        for root, dirs, files in os.walk(source_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Make arcname relative to profiles_dir so it preserves the profile folder name
                                arcname = os.path.relpath(file_path, self.profile_manager.profiles_dir)
                                zipf.write(file_path, arcname)
                        exported_count += 1

            QMessageBox.information(self, "Export Successful", f"Successfully exported {exported_count} profiles to:\n{export_file}")
        except Exception as e:
            logger.error(f"Failed to export ZIP: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export profiles: {e}")

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

    def start_selected_profiles(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection", "Please select at least one profile to start.")
            return

        custom_url = self.custom_url_input.text().strip()

        for row in selected_rows:
            profile_name = self.table.item(row, 2).text()
            profile_id = int(self.table.item(row, 1).text())

            # Get full profile data to get proxy
            profile_data = self.profile_manager.get_profile_by_id(profile_id)
            proxy_info = None
            if profile_data and profile_data['proxy_id']:
                proxy_info = self.proxy_manager.get_proxy_by_id(profile_data['proxy_id'])

            task = BrowserLaunchTask(profile_id, profile_name, proxy_info, custom_url)

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
