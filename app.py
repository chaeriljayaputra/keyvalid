from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# ============ KONFIGURASI ============
DEFAULT_KEYS = {
    "SIYUSUF": {"name": "Permanent User", "exp": "2099-12-31", "created_at": "2024-01-01"},
    "ARYA": {"name": "ARYA User", "exp": "2026-06-15", "created_at": "2024-01-01"},
    "P01": {"name": "1Day User", "exp": "2026-06-12", "created_at": "2024-01-01"},
    "FKPO54": {"name": "Khusus Yang PO OB54", "exp": "2026-06-15", "created_at": "2024-01-01"},
    "YANZ": {"name": "Permanent User", "exp": "2099-12-31", "created_at": "2024-01-01"},
}

DATABASE = {}
REQUEST_LOGS = []  # Menyimpan log di memory (akan reset saat deploy)
IP_STATS = defaultdict(lambda: {"count": 0, "first_seen": None, "last_seen": None})
KEY_STATS = defaultdict(lambda: {"count": 0, "last_used": None, "last_ip": None})

def load_keys():
    global DATABASE
    DATABASE.clear()
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = value.copy()
    print(f"[LOAD] Loaded {len(DATABASE)} default keys")

def is_expired(expiry_date_str):
    return datetime.now().strftime('%Y-%m-%d') > expiry_date_str

load_keys()

# ============ LOGGING ============
def log_request(endpoint, key_used, status_code, success, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')[:50]
    
    log_entry = {
        "timestamp": timestamp,
        "ip": ip,
        "endpoint": endpoint,
        "key": key_used,
        "status": status_code,
        "success": success,
        "user_agent": user_agent,
        "message": message
    }
    REQUEST_LOGS.append(log_entry)
    
    # Update IP Stats
    if IP_STATS[ip]["first_seen"] is None:
        IP_STATS[ip]["first_seen"] = timestamp
    IP_STATS[ip]["last_seen"] = timestamp
    IP_STATS[ip]["count"] += 1
    
    # Update Key Stats (hanya jika key tidak None)
    if key_used and key_used != "None":
        KEY_STATS[key_used]["count"] += 1
        KEY_STATS[key_used]["last_used"] = timestamp
        KEY_STATS[key_used]["last_ip"] = ip

# ============ ROUTES ============

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if not key:
        log_request('/check', None, 400, False, "Key kosong")
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        log_request('/check', key, 404, False, f"Key '{key}' tidak ditemukan")
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    
    if is_expired(key_info['exp']):
        log_request('/check', key, 403, False, f"Key expired pada {key_info['exp']}")
        return jsonify({"success": False, "message": f"Key sudah expired pada {key_info['exp']}"}), 403
    
    log_request('/check', key, 200, True, "Key valid")
    return jsonify({
        "success": True, 
        "message": "Key valid", 
        "data": {"name": key_info['name'], "exp": key_info['exp']}
    })

@app.route('/generate', methods=['GET'])
def generate_key():
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    days_exp = request.args.get('exp', 30)
    name = request.args.get('name', 'Unknown')
    
    if admin_key != 'admin123':
        log_request('/generate', key, 401, False, "Unauthorized")
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if not key:
        log_request('/generate', None, 400, False, "Key kosong")
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    try:
        days_exp = int(days_exp)
    except:
        log_request('/generate', key, 400, False, "exp harus angka")
        return jsonify({"success": False, "message": "exp harus angka"}), 400
    
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }
    
    log_request('/generate', key, 200, True, f"Key created, expires {expiry_date}")
    return jsonify({"success": True, "message": "Key berhasil dibuat", "data": DATABASE[key]})

@app.route('/listkey001', methods=['GET'])
def list_keys():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        log_request('/listkey001', None, 401, False, "Unauthorized")
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    result = {}
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        result[key] = {**info, "status": status}
    
    log_request('/listkey001', None, 200, True, f"Listed {len(DATABASE)} keys")
    return jsonify({"success": True, "total_keys": len(DATABASE), "data": result})

@app.route('/delete', methods=['GET'])
def delete_key():
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    
    if admin_key != 'admin123':
        log_request('/delete', key, 401, False, "Unauthorized")
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if not key:
        log_request('/delete', None, 400, False, "Key kosong")
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        log_request('/delete', key, 404, False, "Key tidak ditemukan")
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    deleted_data = DATABASE.pop(key)
    log_request('/delete', key, 200, True, f"Key {key} deleted")
    return jsonify({"success": True, "message": f"Key '{key}' berhasil dihapus", "data": deleted_data})

@app.route('/reset', methods=['GET'])
def reset_keys():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        log_request('/reset', None, 401, False, "Unauthorized")
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    DATABASE.clear()
    load_keys()
    log_request('/reset', None, 200, True, "Database reset")
    return jsonify({"success": True, "message": "Database direset", "total_keys": len(DATABASE)})

# ============ ENDPOINT UNTUK LIHAT LOGS ============

@app.route('/logs', methods=['GET'])
def view_logs():
    """Lihat semua log request (admin only)"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    limit = request.args.get('limit', 100, type=int)
    logs_to_return = REQUEST_LOGS[-limit:]  # ambil terbaru
    
    return jsonify({
        "success": True,
        "total_logs": len(REQUEST_LOGS),
        "logs": logs_to_return
    })

@app.route('/stats', methods=['GET'])
def view_stats():
    """Lihat statistik IP dan Key (admin only)"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # Hitung total success vs failed dari logs
    total_success = sum(1 for log in REQUEST_LOGS if log["success"])
    total_failed = len(REQUEST_LOGS) - total_success
    
    return jsonify({
        "success": True,
        "summary": {
            "total_requests": len(REQUEST_LOGS),
            "successful": total_success,
            "failed": total_failed
        },
        "ip_stats": dict(IP_STATS),
        "key_stats": dict(KEY_STATS)
    })

@app.route('/logs/clear', methods=['GET'])
def clear_logs():
    """Hapus semua logs (admin only)"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    REQUEST_LOGS.clear()
    IP_STATS.clear()
    KEY_STATS.clear()
    
    return jsonify({"success": True, "message": "All logs cleared"})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "success": True,
        "message": "API Key Server Running",
        "endpoints": {
            "check": "/check?key=KEY",
            "list": "/listkey001?admin=admin123",
            "generate": "/generate?admin=admin123&key=KEY&exp=30&name=NAME",
            "delete": "/delete?admin=admin123&key=KEY",
            "reset": "/reset?admin=admin123",
            "logs": "/logs?admin=admin123",
            "stats": "/stats?admin=admin123",
            "clear_logs": "/logs/clear?admin=admin123"
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print(f"Total keys: {len(DATABASE)}")
    app.run(debug=False, host='0.0.0.0', port=5000)
