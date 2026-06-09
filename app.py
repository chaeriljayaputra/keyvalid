from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT (TAMBAHKAN MANUAL DI SINI) ============
# Format: "nama_key": {"name": "owner_name", "exp": "2025-12-31", "days": 30}
# Anda bisa menambah/mengedit key di sini secara manual

DEFAULT_KEYS = {
    "MEMBERSENDI": {
        "name": "Trial User 1D",
        "exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        "created_at": datetime.now().strftime('%Y-%m-%d')
    },
    "ARYA": {
        "name": "ARYA 5d",
        "exp": (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d'),
        "created_at": datetime.now().strftime('%Y-%m-%d')
    },
    "cangfk6": {
        "name": "Permanent User",
        "exp": "2099-12-31",  # Expired tahun 2099 (permanent)
        "created_at": datetime.now().strftime('%Y-%m-%d')
    },
    # ============ TAMBAHKAN KEY BARU DI SINI ============
    # "NAMA_KEY_ANDA": {
    #     "name": "Nama Owner",
    #     "exp": "2026-06-01",  # format YYYY-MM-DD
    #     "created_at": datetime.now().strftime('%Y-%m-%d')
    # },
}
# ============================================================================

# Load database dari DEFAULT_KEYS + environment variables
DATABASE = {}

def load_keys():
    global DATABASE
    
    # 1. Load dari DEFAULT_KEYS
    for key, value in DEFAULT_KEYS.items():
        DATABASE[key] = value.copy()
    
    # 2. Load dari environment variable (opsional, untuk tambah key via Vercel Env)
    env_keys = os.environ.get('API_KEYS', '')
    if env_keys:
        # Format: "key1|name1|exp1,key2|name2|exp2"
        for item in env_keys.split(','):
            parts = item.split('|')
            if len(parts) >= 3:
                key, name, exp = parts[0], parts[1], parts[2]
                DATABASE[key] = {
                    "name": name,
                    "exp": exp,
                    "created_at": datetime.now().strftime('%Y-%m-%d')
                }

# Load keys saat startup
load_keys()

# Helper function untuk cek expired
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
    
    # Cek expired
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
    
    # Filter key yang expired
    valid_keys = {}
    expired_keys = {}
    
    for key, info in DATABASE.items():
        if is_expired(info['exp']):
            expired_keys[key] = info
        else:
            valid_keys[key] = info
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "valid_keys": len(valid_keys),
        "expired_keys": len(expired_keys),
        "data": DATABASE
    })

@app.route('/delete', methods=['GET'])
def delete_key():
    key = request.args.get('key')
    admin_key = request.args.get('admin', '')
    
    # Proteksi sederhana: perlu admin key untuk hapus
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

# Route untuk reset expired keys (bersihkan key yang expired)
@app.route('/clean', methods=['GET'])
def clean_expired():
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized, perlu parameter admin=admin123"}), 401
    
    expired_keys = []
    for key, info in list(DATABASE.items()):
        if is_expired(info['exp']):
            expired_keys.append(key)
            del DATABASE[key]
    
    return jsonify({
        "success": True,
        "message": f"Berhasil membersihkan {len(expired_keys)} key expired",
        "deleted_keys": expired_keys
    })

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print(f"Total keys loaded: {len(DATABASE)}")
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        print(f"  {key} -> {info['name']} ({info['exp']}) [{status}]")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
