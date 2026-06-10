from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
DEFAULT_KEYS = {
    "SIYUSUF": {
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
    "YANZ": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01"
    },
}
# =================================================

DATABASE = {}

def load_keys():
    global DATABASE
    DATABASE.clear()
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = {
            "name": value["name"],
            "exp": value["exp"],
            "created_at": value.get("created_at", datetime.now().strftime('%Y-%m-%d'))
        }
    print(f"[LOAD] Loaded {len(DATABASE)} default keys")

def is_expired(expiry_date_str):
    today = datetime.now().strftime('%Y-%m-%d')
    return today > expiry_date_str

load_keys()

# ============ ROUTES ============

@app.route('/generate', methods=['GET'])
def generate_key():
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    days_exp = request.args.get('exp')
    name = request.args.get('name', 'Unknown')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized, perlu parameter admin=admin123"}), 401
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if days_exp is None:
        days_exp = 30
    else:
        try:
            days_exp = int(days_exp)
        except:
            return jsonify({"success": False, "message": "exp harus angka"}), 400
    
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }
    
    return jsonify({
        "success": True, 
        "message": "Key berhasil dibuat", 
        "data": DATABASE[key]
    })

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    print(f"[CHECK] Key requested: {key}")
    print(f"[CHECK] Available keys: {list(DATABASE.keys())}")
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({
            "success": False, 
            "message": f"Key '{key}' tidak ditemukan"
        }), 404
    
    key_info = DATABASE[key]
    
    if is_expired(key_info['exp']):
        return jsonify({
            "success": False, 
            "message": f"Key sudah expired pada {key_info['exp']}"
        }), 403
    
    return jsonify({
        "success": True, 
        "message": "Key valid", 
        "data": {
            "name": key_info['name'],
            "exp": key_info['exp']
        }
    })

@app.route('/listkey001', methods=['GET'])
def list_keys():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized, perlu parameter admin=admin123"}), 401
    
    if not DATABASE:
        return jsonify({"success": True, "message": "Belum ada key yang terdaftar", "data": {}})
    
    result = {}
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        result[key] = {
            "name": info['name'],
            "exp": info['exp'],
            "created_at": info['created_at'],
            "status": status
        }
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "data": result
    })

@app.route('/delete', methods=['GET'])
def delete_key():
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized, perlu parameter admin=admin123"}), 401
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    deleted_data = DATABASE.pop(key)
    
    return jsonify({
        "success": True, 
        "message": f"Key '{key}' berhasil dihapus",
        "data": deleted_data
    })

@app.route('/reset', methods=['GET'])
def reset_keys():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    DATABASE.clear()
    load_keys()
    
    return jsonify({
        "success": True,
        "message": "Database direset, default keys dimuat ulang",
        "total_keys": len(DATABASE)
    })

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
            "reset": "/reset?admin=admin123"
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print(f"Total keys: {len(DATABASE)}")
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        print(f"  {key} -> {info['name']} (exp: {info['exp']}) [{status}]")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
