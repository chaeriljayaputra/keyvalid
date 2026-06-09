from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# File database
DB_FILE = "key.json"

# ==================== FUNGSI DATABASE ====================
def load_database():
    """Muat database dari key.json"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_database(data):
    """Simpan database ke key.json"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load database saat startup
DATABASE = load_database()

# ==================== ROUTE API ====================
@app.route('/generate', methods=['GET'])
def generate_key():
    key = request.args.get('key')
    days_exp = int(request.args.get('exp', 30))
    name = request.args.get('name', 'Unknown')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    # Reload database terbaru
    DATABASE = load_database()
    
    # Cek apakah key sudah ada
    if key in DATABASE:
        return jsonify({"success": False, "message": "Key sudah ada"}), 409
    
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d')
    }
    
    save_database(DATABASE)
    
    return jsonify({"success": True, "message": "Key berhasil dibuat", "data": DATABASE[key]})

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    # Reload database terbaru
    DATABASE = load_database()
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    today = datetime.now().strftime('%Y-%m-%d')
    
    if today > key_info['exp']:
        # Hapus key yang expired
        del DATABASE[key]
        save_database(DATABASE)
        return jsonify({"success": False, "message": "Key sudah expired", "data": key_info}), 403
    
    return jsonify({"success": True, "message": "Key valid", "data": key_info})

@app.route('/listkey001', methods=['GET'])
def list_keys():
    # Reload database terbaru
    DATABASE = load_database()
    
    if not DATABASE:
        return jsonify({"success": True, "message": "Belum ada key yang terdaftar", "total_keys": 0, "data": {}})
    
    formatted_data = {}
    for key, info in DATABASE.items():
        formatted_data[key] = {
            "name": info.get("name", "Unknown"),
            "exp": info.get("exp"),
            "created_at": info.get("created_at")
        }
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "data": formatted_data
    })

@app.route('/delete', methods=['DELETE'])
def delete_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    # Reload database terbaru
    DATABASE = load_database()
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    deleted_data = DATABASE.pop(key)
    save_database(DATABASE)
    
    return jsonify({
        "success": True, 
        "message": f"Key '{key}' berhasil dihapus",
        "data": deleted_data
    })

@app.route('/clear-all', methods=['DELETE'])
def clear_all():
    count = len(load_database())
    save_database({})
    return jsonify({
        "success": True, 
        "message": f"Semua key ({count}) berhasil dihapus"
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🔑 API Key Manager Running!")
    print("📍 Server: http://127.0.0.1:5000")
    print("💾 Database: key.json (tersimpan aman)")
    print("📝 Endpoints:")
    print("   GET    /generate?key=xxx&exp=1&name=User")
    print("   GET    /check?key=xxx")
    print("   GET    /listkey001")
    print("   DELETE /delete?key=xxx")
    print("   DELETE /clear-all")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)
