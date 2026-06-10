from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

app = Flask(__name__)

# ============ ADMIN DEVICE (isi dengan device kamu) ============
# Cara dapetin device_id: akses /my_device nanti, copy hasilnya
ADMIN_DEVICES = {
    "e1a396b5ff195ad9c4d0bf868b538e43",  # GANTI DENGAN DEVICE KAMU!
}

# ============ DEFAULT KEYS DENGAN PRE-BOUND DEVICE ============
# 
# Cara pakai:
# 1. Kalau mau key sudah terikat ke device tertentu, tambahkan "device_id": "xxx"
# 2. Kalau tidak ditulis, key akan binding otomatis saat pertama dipakai
# 3. max_devices: berapa banyak device yang boleh pakai key ini
#
DEFAULT_KEYS = {
    # ============ KEYS UNTUK ADMIN/TESTING ============
    "hanz": {
        "name": "Hanz Permanent",
        "exp": "2099-12-31",
        "created_at": "2024-01-01",
        "max_devices": 1,
    },

    "003": {
        "name": "User Free Keyy",
        "exp": "2026-06-11",
        "created_at": "2024-01-01",
        "max_devices": 1,
    },
    
    # ============ KEYS PERMANENT (tidak expired) ============
    "SIYUSUF": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01",
        "max_devices": 1,
        # tanpa device_id -> akan binding otomatis saat pertama dipakai
    },
    
    "YANZ": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01",
        "max_devices": 1,
    },
    
    # ============ KEYS DENGAN MASA BERLAKU ============
    "ARYA": {
        "name": "ARYA User", 
        "exp": "2026-06-15",
        "created_at": "2024-01-01",
        "max_devices": 1,
    },
    
    "P01": {
        "name": "1Day User", 
        "exp": "2026-06-12",
        "created_at": "2024-01-01",
        "max_devices": 1,
    },
    
    "FKPO54": {
        "name": "Khusus Yang PO OB54", 
        "exp": "2026-06-15",
        "created_at": "2024-01-01",
        "max_devices": 4,  # bisa 4 device berbeda
    },
    
    "Tyrexuid001": {
        "name": "User 1D", 
        "exp": "2026-06-12",
        "created_at": "2024-01-01",
        "max_devices": 1,
        "device_id": "555d618962e14faa04fc35d9f6b7e5c7"  # pre-bound ke device user
    },
    
    # ============ TAMBAH KEY BARU DI SINI ============
    # Contoh key dengan pre-bound device:
    # "NAMA_KEY": {
    #     "name": "Nama User",
    #     "exp": "2026-12-31",
    #     "created_at": "2024-01-01",
    #     "max_devices": 1,
    #     "device_id": "device_id_nya_disini"
    # },
    #
    # Contoh key tanpa pre-bound (binding otomatis):
    # "NAMA_KEY2": {
    #     "name": "Nama User 2",
    #     "exp": "2026-12-31",
    #     "created_at": "2024-01-01",
    #     "max_devices": 1,
    # },
}

# ============ GLOBAL VARS ============
DATABASE = {}
KEY_BINDINGS = {}
REQUEST_LOGS = []
BLOCKED_ATTEMPTS = []

# ============ HELPER FUNCTIONS ============

def is_admin():
    device_id = get_device_id()
    return device_id in ADMIN_DEVICES

def get_device_id():
    device_id = request.headers.get('X-Device-ID', '')
    if not device_id:
        fingerprint = f"{request.remote_addr}|{request.headers.get('User-Agent', '')}"
        device_id = hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
    return device_id

def bind_key(key, device_id, ip):
    max_devices = DATABASE.get(key, {}).get("max_devices", 1)
    
    if key not in KEY_BINDINGS:
        KEY_BINDINGS[key] = {
            "devices": [device_id],
            "bound_at": datetime.now().isoformat(),
            "bound_ip": ip
        }
        return True, f"Key terikat ke device ini (1/{max_devices})"
    
    binding = KEY_BINDINGS[key]
    
    if device_id in binding["devices"]:
        return True, f"Device sudah terdaftar ({len(binding['devices'])}/{max_devices})"
    
    if len(binding["devices"]) >= max_devices:
        return False, f"⚠️ Key已达最大设备数 {max_devices} 台"
    
    binding["devices"].append(device_id)
    return True, f"Device baru ditambahkan ({len(binding['devices'])}/{max_devices})"

def is_device_allowed(key, device_id):
    if key not in KEY_BINDINGS:
        return True
    return device_id in KEY_BINDINGS[key]["devices"]

def log(endpoint, key, status, success, msg, device_id, blocked=False):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "time": timestamp, "ip": request.remote_addr, "device": device_id[:16],
        "endpoint": endpoint, "key": key, "status": status,
        "success": success, "blocked": blocked, "msg": msg
    }
    REQUEST_LOGS.append(log_entry)
    if blocked:
        BLOCKED_ATTEMPTS.append(log_entry)

def load_keys():
    global DATABASE, KEY_BINDINGS
    DATABASE.clear()
    
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = {
            "name": value["name"],
            "exp": value["exp"],
            "created_at": value.get("created_at", datetime.now().strftime('%Y-%m-%d')),
            "max_devices": value.get("max_devices", 1)
        }
        
        # CEK APAKAH ADA DEVICE_ID OPSIONAL (PRE-BOUND)
        if "device_id" in value and value["device_id"]:
            device_id = value["device_id"]
            if key not in KEY_BINDINGS:
                KEY_BINDINGS[key] = {
                    "devices": [device_id],
                    "bound_at": value.get("created_at", "2024-01-01") + "T00:00:00",
                    "bound_ip": "predefined"
                }
                print(f"[PRE-BOUND] Key '{key}' -> device: {device_id[:16]}...")
            else:
                if device_id not in KEY_BINDINGS[key]["devices"]:
                    KEY_BINDINGS[key]["devices"].append(device_id)
                    print(f"[PRE-BOUND] Key '{key}' add device: {device_id[:16]}...")
    
    print(f"[LOAD] Total keys: {len(DATABASE)}, Pre-bound: {len(KEY_BINDINGS)}")

def is_expired(exp_date):
    return datetime.now().strftime('%Y-%m-%d') > exp_date

# Load keys (auto pre-bound dari DEFAULT_KEYS)
load_keys()

# ============ MAIN API ============

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    device_id = get_device_id()
    
    if not key:
        log('/check', None, 400, False, "Key kosong", device_id)
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        log('/check', key, 404, False, "Key tidak ditemukan", device_id)
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    info = DATABASE[key]
    
    if is_expired(info['exp']):
        log('/check', key, 403, False, f"Key expired {info['exp']}", device_id)
        return jsonify({"success": False, "message": f"Key expired pada {info['exp']}"}), 403
    
    # CEK DEVICE
    if not is_device_allowed(key, device_id):
        binding = KEY_BINDINGS.get(key, {})
        log('/check', key, 403, False, f"Device BLOCKED!", device_id, blocked=True)
        return jsonify({
            "success": False,
            "message": f"⛔ KEY SUDAH TERPAKAI DI DEVICE LAIN! ⛔",
            "bound_devices": len(binding.get("devices", [])),
            "max_devices": info.get("max_devices", 1),
            "your_device": device_id[:16] + "..."
        }), 403
    
    # BINDING OTOMATIS (jika key belum terikat dan tidak ada pre-bound)
    if key not in KEY_BINDINGS:
        success, msg = bind_key(key, device_id, request.remote_addr)
        log('/check', key, 200, True, msg, device_id)
        return jsonify({
            "success": True,
            "message": f"✅ Key valid. {msg}",
            "data": {
                "name": info['name'],
                "exp": info['exp'],
                "bound_devices": 1,
                "max_devices": info.get("max_devices", 1)
            }
        })
    
    # NORMAL (sudah terikat)
    binding = KEY_BINDINGS[key]
    log('/check', key, 200, True, "Key valid", device_id)
    return jsonify({
        "success": True,
        "message": "✅ Key valid",
        "data": {
            "name": info['name'],
            "exp": info['exp'],
            "bound_devices": len(binding["devices"]),
            "max_devices": info.get("max_devices", 1)
        }
    })

@app.route('/activate', methods=['POST'])
def activate_key():
    """Endpoint untuk aktivasi/binding (dipanggil scgen.py)"""
    data = request.get_json() or {}
    key = data.get('key')
    device_id = data.get('device_id')
    
    if not key or not device_id:
        return jsonify({"success": False, "message": "Key dan device_id required"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    info = DATABASE[key]
    
    if is_expired(info['exp']):
        return jsonify({"success": False, "message": f"Key expired pada {info['exp']}"}), 403
    
    # CEK DEVICE
    if not is_device_allowed(key, device_id):
        binding = KEY_BINDINGS.get(key, {})
        max_devices = info.get("max_devices", 1)
        
        if len(binding.get("devices", [])) >= max_devices:
            return jsonify({
                "success": False,
                "message": f"Key sudah terikat ke {len(binding['devices'])} device (maks {max_devices})"
            }), 403
        else:
            # Tambah device baru
            if key not in KEY_BINDINGS:
                KEY_BINDINGS[key] = {"devices": [], "bound_at": "", "bound_ip": ""}
            KEY_BINDINGS[key]["devices"].append(device_id)
            KEY_BINDINGS[key]["bound_at"] = datetime.now().isoformat()
            KEY_BINDINGS[key]["bound_ip"] = request.remote_addr
            return jsonify({
                "success": True,
                "message": f"Device baru ditambahkan ({len(KEY_BINDINGS[key]['devices'])}/{max_devices})",
                "data": {"name": info['name'], "exp": info['exp']}
            })
    else:
        # Device sudah terdaftar
        if key not in KEY_BINDINGS:
            KEY_BINDINGS[key] = {"devices": [device_id], "bound_at": datetime.now().isoformat(), "bound_ip": request.remote_addr}
        return jsonify({
            "success": True,
            "message": "Key valid",
            "data": {"name": info['name'], "exp": info['exp']}
        })

# ============ ADMIN API ============

@app.route('/admin/reset', methods=['POST'])
def admin_reset_binding():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    key = data.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in KEY_BINDINGS:
        return jsonify({"success": False, "message": f"Key '{key}' tidak memiliki binding"}), 404
    
    old = KEY_BINDINGS.pop(key)
    return jsonify({
        "success": True,
        "message": f"✅ Binding key '{key}' telah direset",
        "old_binding": {"devices": old["devices"], "bound_at": old["bound_at"]}
    })

@app.route('/admin/list', methods=['GET'])
def admin_list():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    result = {}
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        binding = KEY_BINDINGS.get(key, {})
        result[key] = {
            "name": info['name'],
            "exp": info['exp'],
            "status": status,
            "max_devices": info.get("max_devices", 1),
            "bound_devices": len(binding.get("devices", [])),
            "devices": binding.get("devices", [])
        }
    
    return jsonify({"success": True, "total": len(result), "keys": result})

@app.route('/admin/create', methods=['POST'])
def admin_create_key():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    key = data.get('key')
    name = data.get('name', 'New User')
    days = data.get('days', 30)
    max_devices = data.get('max_devices', 1)
    device_id = data.get('device_id', None)  # opsional pre-bound
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' sudah ada"}), 400
    
    exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": exp_date,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "max_devices": max_devices
    }
    
    # Jika ada device_id, langsung binding
    if device_id:
        KEY_BINDINGS[key] = {
            "devices": [device_id],
            "bound_at": datetime.now().isoformat(),
            "bound_ip": request.remote_addr
        }
    
    return jsonify({"success": True, "message": f"Key '{key}' berhasil dibuat", "data": DATABASE[key]})

@app.route('/admin/delete', methods=['POST'])
def admin_delete_key():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    key = data.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    del DATABASE[key]
    if key in KEY_BINDINGS:
        del KEY_BINDINGS[key]
    
    return jsonify({"success": True, "message": f"Key '{key}' berhasil dihapus"})

@app.route('/admin/logs', methods=['GET'])
def admin_logs():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        "success": True,
        "total": len(REQUEST_LOGS),
        "blocked": len(BLOCKED_ATTEMPTS),
        "logs": REQUEST_LOGS[-limit:]
    })

@app.route('/admin/blocked', methods=['GET'])
def admin_blocked():
    if not is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    return jsonify({"success": True, "total": len(BLOCKED_ATTEMPTS), "attempts": BLOCKED_ATTEMPTS})

# ============ PUBLIC API ============

@app.route('/my_device', methods=['GET'])
def my_device():
    return jsonify({
        "success": True,
        "device_id": get_device_id(),
        "ip": request.remote_addr,
        "is_admin": is_admin()
    })

@app.route('/verify', methods=['GET'])
def verify():
    key = request.args.get('key')
    if not key:
        return jsonify({"success": False, "message": "Key required"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Invalid key"}), 404
    
    info = DATABASE[key]
    if is_expired(info['exp']):
        return jsonify({"success": False, "message": "Expired", "exp": info['exp']}), 403
    
    return jsonify({
        "success": True,
        "name": info['name'],
        "exp": info['exp'],
        "remaining_days": (datetime.strptime(info['exp'], '%Y-%m-%d') - datetime.now()).days
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "success": True,
        "message": "API Key Server Running",
        "your_device": get_device_id(),
        "is_admin": is_admin(),
        "endpoints": {
            "check": "/check?key=KEY",
            "activate": "POST /activate",
            "verify": "/verify?key=KEY",
            "my_device": "/my_device",
            "admin": {
                "reset_binding": "POST /admin/reset",
                "list_keys": "GET /admin/list",
                "create_key": "POST /admin/create",
                "delete_key": "POST /admin/delete",
                "logs": "GET /admin/logs",
                "blocked": "GET /admin/blocked"
            }
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print(f"Admin Device: {list(ADMIN_DEVICES)}")
    print(f"Total Keys: {len(DATABASE)}")
    print(f"Pre-bound Keys: {len(KEY_BINDINGS)}")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
