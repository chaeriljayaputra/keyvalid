from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
DEFAULT_KEYS = {
    "hanz": {
        "name": "Hanz Permanent",
        "exp": "2099-12-31",
        "created_at": "2024-01-01"
    },
    "rudalkuda": {
        "name": "User 1Day",
        "exp": "2026-06-12",
        "created_at": "2024-01-01"
    },    
    "009": {
        "name": "Free Key 1Day",
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

def get_expiry_time(key_info):
    """Menghitung waktu expired"""
    try:
        # CEK EXPIRED DARI created_at + minutes
        if "exp_minutes" in key_info:
            created = datetime.strptime(key_info.get("created_at", "2024-01-01"), '%Y-%m-%d')
            return created + timedelta(minutes=int(key_info["exp_minutes"]))
        
        # CEK EXPIRED DARI created_at + seconds
        if "exp_seconds" in key_info:
            created = datetime.strptime(key_info.get("created_at", "2024-01-01"), '%Y-%m-%d')
            return created + timedelta(seconds=int(key_info["exp_seconds"]))
        
        # CEK EXPIRED DARI TANGGAL BIASA
        if "exp" in key_info:
            return datetime.strptime(key_info["exp"], '%Y-%m-%d')
            
    except Exception as e:
        print(f"Error parsing expiry: {e}")
    
    return datetime.strptime("2099-12-31", '%Y-%m-%d')

def get_remaining_string(key_info):
    """Sisa waktu dalam format readable"""
    try:
        exp_time = get_expiry_time(key_info)
        now = datetime.now()
        
        if exp_time <= now:
            return "EXPIRED"
        
        remaining = exp_time - now
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        seconds = remaining.seconds % 60
        
        if days > 0:
            return f"{days} hari {hours} jam"
        elif hours > 0:
            return f"{hours} jam {minutes} menit"
        elif minutes > 0:
            return f"{minutes} menit {seconds} detik"
        else:
            return f"{seconds} detik"
    except:
        return "UNKNOWN"

def is_expired(key_info):
    """Cek expired"""
    try:
        exp_time = get_expiry_time(key_info)
        return datetime.now() > exp_time
    except:
        return False

def load_keys():
    global DATABASE
    DATABASE.clear()
    
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = value.copy()
    
    print(f"[LOAD] Total keys: {len(DATABASE)}")

load_keys()

# ============ MAIN API ============

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    info = DATABASE[key]
    
    if is_expired(info):
        return jsonify({"success": False, "message": f"Key sudah expired"}), 403
    
    remaining = get_remaining_string(info)
    
    return jsonify({
        "success": True,
        "message": f"✅ Key valid (sisa {remaining})",
        "data": {
            "name": info['name'],
            "exp": info.get('exp', 'unknown'),
            "remaining": remaining
        }
    })

@app.route('/verify', methods=['GET'])
def verify():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Key required"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Invalid key"}), 404
    
    info = DATABASE[key]
    
    if is_expired(info):
        return jsonify({"success": False, "message": "Expired"}), 403
    
    return jsonify({
        "success": True,
        "name": info['name'],
        "exp": info.get('exp', 'unknown')
    })

# ============ ADMIN API ============

@app.route('/admin/list', methods=['GET'])
def admin_list():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    result = {}
    for key, info in DATABASE.items():
        expired = is_expired(info)
        status = "EXPIRED" if expired else "VALID"
        
        result[key] = {
            "name": info['name'],
            "exp": info.get('exp', 'unknown'),
            "status": status,
            "remaining": get_remaining_string(info) if not expired else "EXPIRED"
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

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
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

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "success": True,
        "message": "API Key Server Running",
        "total_keys": len(DATABASE),
        "endpoints": {
            "check": "/check?key=KEY",
            "verify": "/verify?key=KEY",
            "list": "/admin/list?admin=admin123",
            "create": "POST /admin/create?admin=admin123",
            "delete": "POST /admin/delete?admin=admin123",
            "reset": "POST /admin/reset?admin=admin123"
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print(f"Total Keys: {len(DATABASE)}")
    for key, info in DATABASE.items():
        status = "✅" if not is_expired(info) else "❌"
        print(f"  {status} {key} -> {info['name']}")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
