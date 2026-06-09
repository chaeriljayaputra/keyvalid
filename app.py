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
    
    # Cek duplikat
    if key in DATABASE:
        return jsonify({"success": False, "message": "Key sudah ada"}), 409
    
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
    today = datetime.now().strftime('%Y-%m-%d')
    
    if today > key_info['exp']:
        # Hapus key yang expired
