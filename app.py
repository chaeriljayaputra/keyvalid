from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Simulasi database
DATABASE = {}

# --- Route Existing ---
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
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    if datetime.now().strftime('%Y-%m-%d') > key_info['exp']:
        return jsonify({"success": False, "message": "Key sudah expired", "data": key_info}), 403
    
    return jsonify({"success": True, "message": "Key valid", "data": key_info})

# --- Fitur Baru: List Key ---
@app.route('/listkey001', methods=['GET'])
def list_keys():
    if not DATABASE:
        return jsonify({"success": True, "message": "Belum ada key yang terdaftar", "data": {}})
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "data": DATABASE
    })

# --- Fitur Baru: Hapus Key ---
@app.route('/delete', methods=['GET'])
def delete_key():
    key = request.args.get('key')
    
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
    app.run(debug=False)
