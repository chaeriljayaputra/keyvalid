from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
DEFAULT_KEYS = {
    "hanz": {
        "name": "Hanz Permanent",
        "exp": "2099-12-31",
        "created_at": "2024-01-01"
    },
    "009": {
        "name": "FreeKey",
        "exp": "2026-06-12",
        "created_at": "2024-01-01"
    },
    "padilhandsome": {
        "name": "User 1Day",
        "exp": "2026-06-12",
        "created_at": "2024-01-01"
    },
    "SIYUSUF": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01"
    },
    "YANZ": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01"
    },
    "ARYA": {
        "name": "ARYA User", 
        "exp": "2026-06-15",
        "created_at": "2024-01-01"
    },
    "P01": {
        "name": "1Day User", 
        "exp": "2026-06-12",
        "created_at": "2024-01-01"
    },
    "FKPO54": {
        "name": "Khusus Yang PO OB54", 
        "exp": "2026-06-15",
        "created_at": "2024-01-01"
    },
    "Tyrexuid001": {
        "name": "User 1D", 
        "exp": "2026-06-12",
        "created_at": "2024-01-01"
    },
}

# ============ GLOBAL VARS ============
DATABASE = {}
REQUEST_LOGS = []

# ============ HELPER FUNCTIONS ============

def log(endpoint, key, status, success, msg, ip):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "time": timestamp,
        "ip": ip,
        "endpoint": endpoint,
        "key": key,
        "status": status,
        "success": success,
        "msg": msg
    }
    REQUEST_LOGS.append(log_entry)

def load_keys():
    global DATABASE
    DATABASE.clear()
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = {
            "name": value["name"],
            "exp": value["exp"],
            "created_at": value.get("created_at", datetime.now().strftime('%Y-%m-%d'))
        }
    print(f"[LOAD] Loaded {len(DATABASE)} keys")

def is_expired(exp_date):
    return datetime.now().strftime('%Y-%m-%d') > exp_date

load_keys()

# ============ MAIN API ============

@app.route('/check', methods=['GET'])
def check_key():
    """Cek key - endpoint utama"""
    key = request.args.get('key')
    ip = request.remote_addr
    
    if not key:
        log('/check', None, 400, False, "Key kosong", ip)
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        log('/check', key, 404, False, "Key tidak ditemukan", ip)
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    info = DATABASE[key]
    
    if is_expired(info['exp']):
        log('/check', key, 403, False, f"Key expired {info['exp']}", ip)
        return jsonify({"success": False, "message": f"Key expired pada {info['exp']}"}), 403
    
    log('/check', key, 200, True, "Key valid", ip)
    return jsonify({
        "success": True,
        "message": "✅ Key valid",
        "data": {
            "name": info['name'],
            "exp": info['exp']
        }
    })

@app.route('/verify', methods=['GET'])
def verify():
    """Cek key versi sederhana"""
    key = request.args.get('key')
    ip = request.remote_addr
    
    if not key:
        return jsonify({"success": False, "message": "Key required"}), 400
    
    if key not in DATABASE:
        log('/verify', key, 404, False, "Key tidak ditemukan", ip)
        return jsonify({"success": False, "message": "Invalid key"}), 404
    
    info = DATABASE[key]
    if is_expired(info['exp']):
        log('/verify', key, 403, False, f"Key expired {info['exp']}", ip)
        return jsonify({"success": False, "message": "Expired", "exp": info['exp']}), 403
    
    log('/verify', key, 200, True, "Key valid", ip)
    return jsonify({
        "success": True,
        "name": info['name'],
        "exp": info['exp'],
        "remaining_days": (datetime.strptime(info['exp'], '%Y-%m-%d') - datetime.now()).days
    })

# ============ ADMIN API (dengan password) ============

@app.route('/admin/list', methods=['GET'])
def admin_list():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    result = {}
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        result[key] = {
            "name": info['name'],
            "exp": info['exp'],
            "created_at": info['created_at'],
            "status": status
        }
    
    return jsonify({"success": True, "total": len(result), "keys": result})

@app.route('/admin/create', methods=['POST'])
def admin_create_key():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    key = data.get('key')
    name = data.get('name', 'New User')
    days = data.get('days', 30)
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' sudah ada"}), 400
    
    exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": exp_date,
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }
    
    return jsonify({"success": True, "message": f"Key '{key}' berhasil dibuat", "data": DATABASE[key]})

@app.route('/admin/delete', methods=['POST'])
def admin_delete_key():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    key = data.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    del DATABASE[key]
    
    return jsonify({"success": True, "message": f"Key '{key}' berhasil dihapus"})

@app.route('/admin/logs', methods=['GET'])
def admin_logs():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        "success": True,
        "total": len(REQUEST_LOGS),
        "logs": REQUEST_LOGS[-limit:]
    })

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    """Reset ke default keys"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    DATABASE.clear()
    load_keys()
    
    return jsonify({
        "success": True,
        "message": "Database direset ke default keys",
        "total_keys": len(DATABASE)
    })

# ============ PUBLIC API ============

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "success": True,
        "message": "API Key Server Running",
        "total_keys": len(DATABASE),
        "endpoints": {
            "check": "/check?key=KEY",
            "verify": "/verify?key=KEY",
            "admin": {
                "list_keys": "/admin/list?admin=admin123",
                "create_key": "POST /admin/create?admin=admin123",
                "delete_key": "POST /admin/delete?admin=admin123",
                "logs": "/admin/logs?admin=admin123",
                "reset": "POST /admin/reset?admin=admin123"
            }
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY (No Device Binding)")
    print("="*50)
    print(f"Total Keys: {len(DATABASE)}")
    print("\n📋 DAFTAR KEY:")
    for key, info in DATABASE.items():
        status = "✅" if not is_expired(info['exp']) else "❌"
        print(f"  {status} {key} -> {info['name']} (exp: {info['exp']})")
    print("="*50)
    print("\n🔑 Admin Password: admin123")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
