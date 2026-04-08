// Global state
let profilesData = [];

// Initialize
async function init() {
    await loadGroups();
    await loadProfiles();
    startSysMonitor();
}

async function loadGroups() {
    const groups = await eel.get_groups()();
    const select = document.getElementById('groupFilter');
    const current = select.value;
    select.innerHTML = '<option value="All Groups">All Groups</option>';
    groups.forEach(g => {
        if(g !== "All Groups") {
            const opt = document.createElement('option');
            opt.value = g;
            opt.innerText = g;
            select.appendChild(opt);
        }
    });
    if([...select.options].some(o => o.value === current)) {
        select.value = current;
    }
}

async function loadProfiles() {
    const group = document.getElementById('groupFilter').value;
    profilesData = await eel.get_profiles(group)();

    const tbody = document.getElementById('profilesTableBody');
    tbody.innerHTML = '';

    profilesData.forEach(p => {
        const proxyStr = (p.ip && p.port) ? `${p.ip}:${p.port}` : 'None';
        let statusColor = 'text-subtext';
        if(p.status === 'Running') statusColor = 'text-success';
        if(p.status === 'Failed' || p.status === 'Error') statusColor = 'text-danger';

        const tr = document.createElement('tr');
        tr.className = 'profile-row bg-surface2 border-b border-surface hover:bg-surface transition';
        tr.innerHTML = `
            <td class="p-4 w-10">
                <input type="checkbox" class="profile-cb rounded bg-bg border-surface text-primary focus:ring-primary" value="${p.id}">
            </td>
            <td class="px-4 py-3 font-mono">${p.id}</td>
            <td class="px-4 py-3 font-semibold text-text">${p.name}</td>
            <td class="px-4 py-3">${p.group_name || 'Default'}</td>
            <td class="px-4 py-3 font-mono text-xs">${proxyStr}</td>
            <td class="px-4 py-3 font-bold ${statusColor}" id="status-${p.id}">${p.status || 'Unknown'}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('selectAll').checked = false;
}

function toggleSelectAll() {
    const state = document.getElementById('selectAll').checked;
    document.querySelectorAll('.profile-cb').forEach(cb => cb.checked = state);
}

function getSelectedIds() {
    return Array.from(document.querySelectorAll('.profile-cb:checked')).map(cb => cb.value);
}

function showLoader(text) {
    document.getElementById('loader-text').innerText = text;
    document.getElementById('loader').classList.remove('hidden');
}
function hideLoader() {
    document.getElementById('loader').classList.add('hidden');
}

// Actions
async function createBulk() {
    const prefix = prompt("Enter profile prefix (e.g., fb_acc):");
    if(!prefix) return;
    const count = prompt("How many profiles to create?");
    if(!count || isNaN(count)) return;
    const group = prompt("Enter group name (leave empty for Default):");

    showLoader("Creating profiles...");
    const res = await eel.create_bulk_profiles(prefix, parseInt(count), group)();
    hideLoader();
    alert(res.message);
    await init();
}

async function deleteSelected() {
    const ids = getSelectedIds();
    if(ids.length === 0) return alert("Select profiles first.");
    if(!confirm(`Delete ${ids.length} profiles?`)) return;

    showLoader("Deleting profiles...");
    const res = await eel.delete_profiles(ids)();
    hideLoader();
    alert(res.message);
    await loadProfiles();
}

async function scanProfiles() {
    const dir = await eel.pick_directory()();
    if(!dir) return;

    showLoader("Scanning...");
    const res = await eel.scan_profiles(dir)();
    hideLoader();

    if(res.status === 'success' && res.found.length > 0) {
        if(confirm(`Found ${res.found.length} profiles. Register them in DB?`)) {
            showLoader("Registering...");
            const regRes = await eel.confirm_scan(dir, res.found)();
            hideLoader();
            alert(regRes.message);
            await init();
        }
    } else {
        alert(res.message || "No profiles found.");
    }
}

async function cleanupFiles() {
    if(!confirm("Clear Cache/Temp files for all profiles? Sessions will be saved.")) return;
    const btn = document.getElementById('btn-cleanup');
    btn.disabled = true;
    btn.innerText = "Cleaning...";
    const res = await eel.cleanup_profiles()();
    btn.disabled = false;
    btn.innerText = "Cleanup";
    alert(res.message);
}

async function importProfiles() {
    const file = await eel.pick_file("Select ZIP Profile Backup", [["ZIP Files", "*.zip"]])();
    if(!file) return;

    showLoader("Importing ZIP...");
    const res = await eel.import_profiles(file)();
    hideLoader();
    alert(res.message);
    if(res.status === 'success') await init();
}

async function exportProfiles() {
    const ids = getSelectedIds();
    if(ids.length === 0) return alert("Select profiles to export.");

    const file = await eel.pick_save_file("Save Export as ZIP", "profiles_backup.zip", [["ZIP Files", "*.zip"]])();
    if(!file) return;

    showLoader("Exporting ZIP...");
    const res = await eel.export_profiles(ids, file)();
    hideLoader();
    alert(res.message);
}

async function startAutoLogin() {
    const ids = getSelectedIds();
    if(ids.length === 0) return alert("Select profiles to auto-login.");

    const file = await eel.pick_file("Select Credentials File", [["Text Files", "*.txt"]])();
    if(!file) return;

    let threads = 50;
    const oneByOne = document.getElementById('oneByOne').checked;
    if(!oneByOne && ids.length > 3) {
        let t = prompt("How many profiles to run concurrently?", "5");
        if(t) threads = parseInt(t);
    } else if(oneByOne) {
        threads = 1;
    }

    showLoader("Starting Auto Login...");
    const res = await eel.launch_auto_login(ids, file, threads)();
    hideLoader();
    alert(res.message);
}

async function manageProxies() {
    document.getElementById('proxyModal').classList.remove('hidden');
    await loadProxies();
}

async function loadProxies() {
    const proxies = await eel.get_proxies()();
    const tbody = document.getElementById('proxyTableBody');
    tbody.innerHTML = '';

    proxies.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = 'border-b border-surface hover:bg-surface transition';
        tr.innerHTML = `
            <td class="px-3 py-2 font-mono">${p.id}</td>
            <td class="px-3 py-2">${p.ip}:${p.port}</td>
            <td class="px-3 py-2">${p.status}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function addProxy() {
    const input = document.getElementById('proxyInput');
    const val = input.value.trim();
    if(!val) return;

    const res = await eel.add_proxy(val)();
    if(res.status === 'success') {
        input.value = '';
        await loadProxies();
    } else {
        alert(res.message);
    }
}

async function assignProxy() {
    const ids = getSelectedIds();
    if(ids.length === 0) return alert("Select profiles to assign proxy.");

    const proxies = await eel.get_proxies()();
    let promptMsg = "Enter Proxy ID from the list below, or 'None' to remove:\n\n";
    proxies.forEach(p => {
        promptMsg += `ID: ${p.id} -> ${p.ip}:${p.port}\n`;
    });

    const proxyId = prompt(promptMsg);
    if(proxyId !== null) {
        showLoader("Assigning...");
        const res = await eel.assign_proxy(ids, proxyId)();
        hideLoader();
        alert(res.message);
        await loadProfiles();
    }
}

async function startSelected() {
    const ids = getSelectedIds();
    if(ids.length === 0) return alert("Select profiles to start.");

    let threads = 50;
    const oneByOne = document.getElementById('oneByOne').checked;
    if(!oneByOne && ids.length > 3) {
        let t = prompt("How many profiles to run concurrently?", "5");
        if(t) threads = parseInt(t);
    }

    const customUrl = document.getElementById('customUrl').value;
    await eel.launch_profiles(ids, customUrl, oneByOne, threads)();
}

// Callbacks from Python
eel.expose(update_profile_status);
function update_profile_status(pid, status) {
    const el = document.getElementById(`status-${pid}`);
    if(el) {
        el.innerText = status;
        el.className = 'px-4 py-3 font-bold ';
        if(status === 'Running') el.className += 'text-success';
        else if(status === 'Failed' || status === 'Error') el.className += 'text-danger';
        else el.className += 'text-subtext';
    }
}

eel.expose(append_log);
function append_log(level, msg) {
    const logBox = document.getElementById('logContent');
    const div = document.createElement('div');
    div.innerText = msg;
    if(level === 'ERROR' || level === 'CRITICAL') div.className = 'text-danger';
    else if(level === 'WARNING') div.className = 'text-warning';
    else if(level === 'INFO') div.className = 'text-success';
    else div.className = 'text-subtext';

    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
}

// System Monitor loop
function startSysMonitor() {
    setInterval(async () => {
        const stats = await eel.get_system_stats()();
        if(stats) {
            document.getElementById('sys-monitor').innerText = `CPU: ${stats.cpu_percent}% | RAM: ${stats.ram_percent}%`;
        }
    }, 2000);
}

// Start
window.onload = init;
