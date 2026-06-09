from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Simulasi database untuk menyimpan kunci
# Format: {"KEY_VALUE": {"name": "Nama", "exp": "YYYY-MM-DD"}}
DATABASE = {}

@app.route('/generate', methods=['GET'])
def generate_key():
    key = request.args.get('key')
    days_exp = int(request.args.get('exp', 30)) # Default 30 hari
    name = request.args.get('name', 'Unknown')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    # Hitung tanggal kedaluwarsa
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    # Simpan ke database
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date
    }
    
    return jsonify({
        "success": True,
        "message": f"Key {key} berhasil dibuat",
        "data": DATABASE[key]
    })

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    # Cek apakah sudah expired
    if datetime.now().strftime('%Y-%m-%d') > key_info['exp']:
        return jsonify({"success": False, "message": "Key sudah expired", "data": key_info}), 403
    
    return jsonify({
        "success": True,
        "message": "Key valid",
        "data": key_info
    })

if __name__ == '__main__':
    app.run(debug=True)
