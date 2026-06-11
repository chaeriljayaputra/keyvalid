from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
#
# FORMAT WAKTU YANG DIDUKUNG:
# 1. "exp": "2026-12-31"           -> expired tanggal (scgen.py pakai ini)
# 2. "exp_minutes": 50             -> expired dalam 50 menit
# 3. "exp_seconds": 3600           -> expired dalam 3600 detik
# 4. "exp_datetime": "2026-06-11 23:59:59" -> expired tepat jam tsb
#
# PRIORITAS: exp_datetime > exp_minutes > exp_seconds > exp
#

DEFAULT_KEYS = {
    # ============ KEYS LAMA (TIDAK BERUBAH) ============
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
    
    # ============ CONTOH KEY DENGAN EXPIRED MENIT ============
    "CONTOH50MENIT": {
        "name": "Contoh Key 50 Menit",
        "exp": "2099-12-31",
        "exp_minutes": 50,
        "created_at": "2024-01-01"
    },
    
    "CONTOH30MENIT": {
        "name": "Contoh Key 30 Menit",
        "exp": "2099-12-31",
        "exp_minutes": 30,
        "created_at": "2024-01-01"
    },
    
    "CONTOH10MENIT": {
        "name": "Contoh Key 10 Menit",
        "exp": "2099-12-31",
        "exp_minutes": 10,
        "created_at": "2024-01-01"
    },
    
    # ============ CONTOH KEY DENGAN EXPIRED DETIK ============
    "CONTOH3600DETIK": {
        "name": "Contoh Key 1 Jam",
        "exp": "2099-12-31",
        "exp_seconds": 3600,
        "created_at": "2024-01-01"
    },
    
    "CONTOH300DETIK": {
        "name": "Contoh Key 5 Menit",
        "exp": "2099-12-31",
        "exp_seconds": 300,
        "created_at": "2024-01-01"
    },
    
    "CONTOH60DETIK": {
        "name": "Contoh Key 1 Menit",
        "exp": "2099-12-31",
        "exp_seconds": 60,
        "created_at": "2024-01-01"
    },
    
    # ============ CONTOH KEY DENGAN EXPIRED TEPAT JAM ============
    "CONTOHTEPATJAM": {
        "name": "Contoh Expired Tepat Jam",
        "exp": "2099-12-31",
        "exp_datetime": "2026-12-31 23:59:59",
        "created_at": "2024-01-01"
    },
    
    # ============ CONTOH KEY CEPAT UNTUK TESTING ============
    "TESTCEPAT": {
        "name": "Testing Cepat",
        "exp": "2099-12-31",
        "exp_seconds": 10,
        "created_at": "2024-01-01"
    },
}

# ============ GLOBAL VARS ============
DATABASE = {}
REQUEST_LOGS = []

# ============ HELPER FUNCTIONS ============

def get_expiry_time(key_info):
    """Menghitung waktu expired dari berbagai format"""
    now = datetime.now()
    
    # PRIORITAS 1: exp_datetime (format lengkap)
    if "exp_datetime" in key_info:
        try:
            exp = datetime.strptime(key_info["exp_datetime"], '%Y-%m-%d %H:%M:%S')
            return exp
        except:
            pass
    
    # PRIORITAS 2: exp_minutes (menit dari created_at)
    if "exp_minutes" in key_info:
        created = datetime.strptime(key_info.get("created_at", now.strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
        return created + timedelta(minutes=key_info["exp_minutes"])
    
    # PRIORITAS 3: exp_seconds (detik dari created_at)
    if "exp_seconds" in key_info:
        created = datetime.strptime(key_info.get("created_at", now.strftime('%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
        return created + timedelta(seconds=key_info["exp_seconds"])
    
    # PRIORITAS 4: exp (tanggal biasa)
    if "exp" in key_info:
        return datetime.strptime(key_info["exp"], '%Y-%m-%d')
    
    return datetime.max

def get_remaining_string(key_info):
    """Mendapatkan sisa waktu dalam format human readable"""
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

def is_expired(key_info):
    """Cek apakah key sudah expired"""
    exp_time = get_expiry_time(key_info)
    return datetime.now() >= exp_time

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
    
    now = datetime.now()
    for key, value in DEFAULT_KEYS.items():
        if "created_at" not in value:
            value["created_at"] = now.strftime('%Y-%m-%d %H:%M:%S')
        DATABASE[key] = value.copy()
    
    print(f"[LOAD] Total keys: {len(DATABASE)}")
    for key, info in DATABASE.items():
        if is_expired(info):
            print(f"  ❌ {key} -> EXPIRED")
        else:
            remaining = get_remaining_string(info)
            print(f"  ✅ {key} -> {remaining}")

load_keys()

# ============ MAIN API ============

@app.route('/check', methods=['GET'])
def check_key():
    """Cek key - endpoint utama untuk scgen.py"""
    key = request.args.get('key')
    ip = request.remote_addr
    
    if not key:
        log('/check', None, 400, False, "Key kosong", ip)
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        log('/check', key, 404, False, "Key tidak ditemukan", ip)
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    info = DATABASE[key]
    
    # CEK EXPIRED DENGAN PRESISI MENIT/DETIK!
    if is_expired(info):
        exp_time = get_expiry_time(info)
        log('/check', key, 403, False, f"Key expired", ip)
        return jsonify({
            "success": False, 
            "message": f"⏰ Key sudah expired pada {exp_time.strftime('%Y-%m-%d %H:%M:%S')}!"
        }), 403
    
    # KEY VALID
    remaining = get_remaining_string(info)
    log('/check', key, 200, True, f"Key valid, sisa {remaining}", ip)
    
    return jsonify({
        "success": True,
        "message": f"✅ Key valid (sisa {remaining})",
        "data": {
            "name": info['name'],
            "exp": info.get('exp', info.get('exp_datetime', 'unknown')),
            "remaining": remaining
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
    
    if is_expired(info):
        log('/verify', key, 403, False, "Key expired", ip)
        return jsonify({"success": False, "message": "Expired"}), 403
    
    remaining = get_remaining_string(info)
    log('/verify', key, 200, True, f"Key valid, sisa {remaining}", ip)
    
    return jsonify({
        "success": True,
        "name": info['name'],
        "remaining": remaining
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
        remaining = get_remaining_string(info) if not expired else "EXPIRED"
        
        result[key] = {
            "name": info['name'],
            "status": status,
            "remaining": remaining,
            "created_at": info.get('created_at'),
            "exp_config": {
                k: v for k, v in info.items() 
                if k not in ['name', 'created_at']
            }
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
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' sudah ada"}), 400
    
    # Support berbagai format waktu
    if 'minutes' in data:
        info = {
            "name": name,
            "exp": "2099-12-31",
            "exp_minutes": data['minutes'],
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    elif 'seconds' in data:
        info = {
            "name": name,
            "exp": "2099-12-31",
            "exp_seconds": data['seconds'],
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    elif 'exp_datetime' in data:
        info = {
            "name": name,
            "exp": "2099-12-31",
            "exp_datetime": data['exp_datetime'],
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        days = data.get('days', 30)
        exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        info = {
            "name": name,
            "exp": exp_date,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    DATABASE[key] = info
    remaining = get_remaining_string(info)
    
    return jsonify({
        "success": True, 
        "message": f"Key '{key}' berhasil dibuat (sisa {remaining})", 
        "data": info
    })

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
        "message": "API Key Server Running (Support Minutes & Seconds)",
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
    print("API KEY SERVER - SUPPORT MENIT/DETIK")
    print("="*50)
    print(f"Total Keys: {len(DATABASE)}")
    print("\n📋 DAFTAR KEY DENGAN SISA WAKTU:")
    for key, info in DATABASE.items():
        if is_expired(info):
            print(f"  ❌ {key} -> {info['name']} (EXPIRED)")
        else:
            remaining = get_remaining_string(info)
            print(f"  ✅ {key} -> {info['name']} (sisa {remaining})")
    print("="*50)
    print("\n🔑 Admin Password: admin123")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
