import eel
import os
import json
import tkinter as tk
from tkinter import filedialog
from src.modules.profiles.manager import ProfileManager
from src.modules.proxies.manager import ProxyManager
from src.modules.tasks.queue_manager import TaskQueueManager, BrowserLaunchTask
from src.utils.system import get_system_resources
from src.utils.logger import get_logger

from src.core.licensing import LicenseManager

logger = get_logger("APIBridge")

profile_manager = ProfileManager()
proxy_manager = ProxyManager()
license_manager = LicenseManager()

@eel.expose
def get_hwid():
    return license_manager.get_hwid()

@eel.expose
def open_buy_link():
    import webbrowser
    buy_link = license_manager.config.get("buy_link", "https://wa.me/1234567890")
    hwid = license_manager.get_hwid()
    full_link = f"{buy_link}?text=Hi,%20I%20want%20to%20buy%20the%20software.%20My%20HWID%20is:%20{hwid}"
    webbrowser.open(full_link)
task_queue = TaskQueueManager()

# Hidden root window for tkinter file dialogs
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

@eel.expose
def get_system_stats():
    return get_system_resources()

@eel.expose
def get_groups():
    return profile_manager.get_all_groups()

@eel.expose
def get_profiles(group_name="All Groups"):
    profiles = profile_manager.get_profiles_by_group(group_name)
    # Convert datetime to string for JSON serialization
    res = []
    for p in profiles:
        p_dict = dict(p)
        if p_dict.get('created_at'):
            p_dict['created_at'] = str(p_dict['created_at']).split('.')[0]
        res.append(p_dict)
    return res

@eel.expose
def create_bulk_profiles(prefix, count, group_name):
    if not group_name:
        group_name = "Default"
    profile_manager.bulk_create_profiles(prefix, int(count), group_name)
    return {"status": "success", "message": f"Successfully created {count} profiles."}

@eel.expose
def delete_profiles(profile_ids):
    deleted = 0
    for pid in profile_ids:
        if profile_manager.delete_profile(int(pid), delete_files=True):
            deleted += 1
    return {"status": "success", "message": f"Deleted {deleted} profiles."}

@eel.expose
def assign_group(profile_ids, group_name):
    group_name = group_name.strip() if group_name.strip() else "Default"
    for pid in profile_ids:
        profile_manager.db.execute("UPDATE profiles SET group_name = ? WHERE id = ?", (group_name, int(pid)))
    return {"status": "success", "message": f"Assigned group '{group_name}' to {len(profile_ids)} profiles."}

@eel.expose
def assign_proxy(profile_ids, proxy_id):
    proxy_id = int(proxy_id) if proxy_id and proxy_id != "None" else None
    for pid in profile_ids:
        profile_manager.db.execute("UPDATE profiles SET proxy_id = ? WHERE id = ?", (proxy_id, int(pid)))
    return {"status": "success", "message": f"Proxy assigned successfully."}

@eel.expose
def get_proxies():
    return [dict(p) for p in proxy_manager.get_all_proxies()]

@eel.expose
def add_proxy(proxy_str):
    parts = proxy_str.strip().split(":")
    if len(parts) >= 2:
        proxy_manager.add_proxy(parts[0], parts[1], parts[2] if len(parts)>2 else None, parts[3] if len(parts)>3 else None)
        return {"status": "success"}
    return {"status": "error", "message": "Invalid format"}

@eel.expose
def launch_profiles(profile_ids, custom_url, one_by_one, thread_count):
    if one_by_one:
        task_queue.set_max_threads(1)
    else:
        task_queue.set_max_threads(int(thread_count))

    for pid in profile_ids:
        pid = int(pid)
        profile_data = profile_manager.get_profile_by_id(pid)
        if not profile_data:
            continue

        proxy_info = None
        if profile_data['proxy_id']:
            proxy_info = proxy_manager.get_proxy_by_id(profile_data['proxy_id'])

        ext_path = profile_data['external_path'] if 'external_path' in profile_data.keys() else None

        task = BrowserLaunchTask(pid, profile_data['name'], proxy_info, custom_url, external_path=ext_path)

        # Update DB status
        profile_manager.update_profile_status(pid, "Pending")
        eel.update_profile_status(pid, "Pending")()

        task_queue.add_task(task)

    return {"status": "success", "message": f"Queued {len(profile_ids)} profiles to launch."}

@eel.expose
def pick_directory():
    path = filedialog.askdirectory(title="Select Directory")
    return path

@eel.expose
def pick_file(title="Select File", filetypes=[("All Files", "*.*")]):
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    return path

@eel.expose
def pick_save_file(title="Save File", default_name="", filetypes=[("All Files", "*.*")]):
    path = filedialog.asksaveasfilename(title=title, initialfile=default_name, filetypes=filetypes)
    return path

@eel.expose
def scan_profiles(dir_path):
    if not dir_path or not os.path.exists(dir_path):
        return {"status": "error", "message": "Invalid directory."}

    found = []
    for item in os.listdir(dir_path):
        if os.path.isdir(os.path.join(dir_path, item)):
            found.append(item)

    return {"status": "success", "found": found}

@eel.expose
def confirm_scan(dir_path, selected_profiles):
    is_same_dir = os.path.normpath(dir_path) == os.path.normpath(profile_manager.profiles_dir)
    added = 0
    for name in selected_profiles:
        existing = profile_manager.db.fetchone("SELECT id FROM profiles WHERE name = ?", (name,))
        if not existing:
            ext_path = None if is_same_dir else dir_path
            profile_manager.create_profile(name, "Imported", external_path=ext_path)
            added += 1
    return {"status": "success", "message": f"Registered {added} profiles."}

@eel.expose
def cleanup_profiles():
    try:
        cleaned, freed_bytes = profile_manager.cleanup_profile_files()
        freed_mb = freed_bytes / (1024 * 1024)
        return {"status": "success", "message": f"Cleaned {cleaned} profiles. Freed {freed_mb:.2f} MB."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@eel.expose
def export_profiles(profile_ids, export_file):
    import zipfile
    try:
        exported_count = 0
        with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pid in profile_ids:
                p_data = profile_manager.get_profile_by_id(int(pid))
                if not p_data: continue

                profile_name = p_data['name']
                external_path = p_data.get('external_path')

                if external_path:
                    source_path = os.path.join(external_path, profile_name)
                else:
                    source_path = os.path.join(profile_manager.profiles_dir, profile_name)

                if os.path.exists(source_path):
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            base_dir = external_path if external_path else profile_manager.profiles_dir
                            arcname = os.path.relpath(file_path, base_dir)
                            zipf.write(file_path, arcname)
                    exported_count += 1
        return {"status": "success", "message": f"Successfully exported {exported_count} profiles to {export_file}."}
    except Exception as e:
        logger.error(f"Failed to export ZIP: {e}")
        return {"status": "error", "message": str(e)}

@eel.expose
def import_profiles(zip_file_path):
    import zipfile
    try:
        imported_count = 0
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            top_level_dirs = set()
            for name in zip_ref.namelist():
                parts = name.split('/')
                if parts[0]:
                    top_level_dirs.add(parts[0])

            for profile_name in top_level_dirs:
                target_path = os.path.join(profile_manager.profiles_dir, profile_name)
                if not os.path.exists(target_path):
                    members = [m for m in zip_ref.namelist() if m.startswith(profile_name + '/')]
                    zip_ref.extractall(path=profile_manager.profiles_dir, members=members)
                    profile_manager.create_profile(profile_name, "Imported")
                    imported_count += 1
        return {"status": "success", "message": f"Successfully imported {imported_count} profiles."}
    except Exception as e:
        logger.error(f"Failed to import ZIP: {e}")
        return {"status": "error", "message": str(e)}

@eel.expose
def launch_auto_login(profile_ids, credentials_file, thread_count):
    try:
        credentials = []
        with open(credentials_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or 'username' in line.lower():
                    continue
                parts = line.split(',')
                if len(parts) >= 2:
                    credentials.append((parts[0].strip(), parts[1].strip()))

        if not credentials:
            return {"status": "error", "message": "No valid credentials found. Format should be: username,password per line."}

        task_queue.set_max_threads(int(thread_count))

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        queued = 0
        for i, pid in enumerate(profile_ids):
            if i >= len(credentials): break

            pid = int(pid)
            profile_data = profile_manager.get_profile_by_id(pid)
            if not profile_data: continue

            p_name = profile_data['name']
            username, password = credentials[i]
            proxy_info = proxy_manager.get_proxy_by_id(profile_data['proxy_id']) if profile_data['proxy_id'] else None
            ext_path = profile_data.get('external_path')

            def inject_login(driver, u=username, p=password, name=p_name):
                try:
                    logger.info(f"Starting auto-login for {name} ({u})")
                    wait = WebDriverWait(driver, 15)
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@id='email' or @name='email']")))
                    except Exception:
                        logger.info(f"Email field not found for {name}. Already logged in?")
                        return
                    try:
                        cookie_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Allow all cookies' or @title='Decline optional cookies']")))
                        cookie_btn.click()
                        time.sleep(1)
                    except: pass

                    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='email' or @name='email']")))
                    email_field.clear()
                    email_field.send_keys(u)
                    pass_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='pass' or @name='pass']")))
                    pass_field.clear()
                    pass_field.send_keys(p)

                    login_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@name='login' or @id='loginbutton' or @data-testid='royal_login_button'] | //input[@type='submit' and contains(@value, 'Log In')] | //button[@type='submit']")))
                    time.sleep(0.3)
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
                        login_btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", login_btn)
                    logger.info(f"Auto-login submitted for {name}")
                except Exception as e:
                    logger.error(f"Auto-login failed for {name}: {e}")

            task = BrowserLaunchTask(pid, p_name, proxy_info, custom_url="https://www.facebook.com/", external_path=ext_path, automation_callback=inject_login)
            profile_manager.update_profile_status(pid, "Pending")
            try: eel.update_profile_status(pid, "Pending")()
            except: pass

            task_queue.add_task(task)
            queued += 1

        return {"status": "success", "message": f"Queued {queued} profiles for Auto Login."}
    except Exception as e:
        logger.error(f"Failed to start auto login: {e}")
        return {"status": "error", "message": str(e)}
