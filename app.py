from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
# Gunakan TANGGAL FIX, bukan datetime.now()!
# Format: "nama_key": {"name": "owner_name", "exp": "YYYY-MM-DD"}

DEFAULT_KEYS = {
    "MEMBERSENDI": {
        "name": "Trial User",
        "exp": "2026-06-10",  # ← TANGGAL FIX, tidak berubah walau redeploy
        "created_at": "2024-01-01"
    },
    "ARYA": {
        "name": "ARYA User", 
        "exp": "2026-06-15",  # ← TANGGAL FIX
        "created_at": "2024-01-01"
    },
    "tsyaa": {
        "name": "Permanent User",
        "exp": "2099-12-31",  # ← Permanent
        "created_at": "2024-01-01"
    },
    # Tambah key baru di sini dengan tanggal fix
    # "KEY_ANDA": {
    #     "name": "Nama Owner",
    #     "exp": "2025-12-31",
    #     "created_at": "2024-01-01"
    # },
}
# ===================================================

DATABASE = {}

def load_keys():
    global DATABASE
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = value.copy()

def is_expired(expiry_date_str):
    return datetime.now().strftime('%Y-%m-%d') > expiry_date_str

# ============ ROUTES ============

@app.route('/generate', methods=['GET'])
def generate_key():
    key = request.args.get('key')
    days_exp = int(request.args.get('exp', 30))
    name = request.args.get('name', 'Unknown')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }
    
    return jsonify({"success": True, "message": "Key berhasil dibuat", "data": DATABASE[key]})

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    
    if is_expired(key_info['exp']):
        return jsonify({
            "success": False, 
            "message": "Key sudah expired", 
            "data": key_info
        }), 403
    
    return jsonify({
        "success": True, 
        "message": "Key valid", 
        "data": key_info
    })

@app.route('/listkey001', methods=['GET'])
def list_keys():
    if not DATABASE:
        return jsonify({"success": True, "message": "Belum ada key yang terdaftar", "data": {}})
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "data": DATABASE
    })

@app.route('/delete', methods=['GET'])
def delete_key():
    key = request.args.get('key')
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
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

if __name__ == '__main__':
    print("API KEY SERVER READY")
    print(f"Total keys: {len(DATABASE)}")
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        print(f"  {key} -> {info['name']} ({info['exp']}) [{status}]")
    app.run(debug=False)
