from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os
import hashlib

app = Flask(__name__)

# ============ KONFIGURASI KEY DEFAULT ============
DEFAULT_KEYS = {
    "MEMBERSENDI": {
        "name": "Trial User",
        "exp": "2025-12-31",
        "created_at": "2024-01-01",
        "bound_device": None,      # TAMBAH: device terikat
        "activated_at": None       # TAMBAH: waktu aktivasi
    },
    "ARYA": {
        "name": "ARYA User", 
        "exp": "2026-06-15",
        "created_at": "2024-01-01",
        "bound_device": None,
        "activated_at": None
    },
    "YANZZZZ": {
        "name": "YANZ User", 
        "exp": "2099-12-30",
        "created_at": "2024-01-01",
        "bound_device": None,
        "activated_at": None
    },
    "YANZ": {
        "name": "Permanent User",
        "exp": "2099-12-31",
        "created_at": "2024-01-01",
        "bound_device": None,
        "activated_at": None
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
            "created_at": value.get("created_at", datetime.now().strftime('%Y-%m-%d')),
            "bound_device": value.get("bound_device"),      # TAMBAH
            "activated_at": value.get("activated_at")       # TAMBAH
        }
    print(f"[LOAD] Loaded {len(DATABASE)} default keys")

def is_expired(expiry_date_str):
    today = datetime.now().strftime('%Y-%m-%d')
    return today > expiry_date_str

# Load keys saat startup
load_keys()

# ============ ROUTES ============

@app.route('/generate', methods=['GET'])
def generate_key():
    key = request.args.get('key')
    days_exp = request.args.get('exp')
    name = request.args.get('name', 'Unknown')
    
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
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "bound_device": None,      # TAMBAH
        "activated_at": None       # TAMBAH
    }
    
    return jsonify({
        "success": True, 
        "message": "Key berhasil dibuat", 
        "data": DATABASE[key]
    })

@app.route('/activate', methods=['POST'])  # <-- ENDPOINT BARU UNTUK BINDING
def activate_key():
    """Endpoint untuk aktivasi key dengan binding device"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400
    
    key = data.get('key')
    device_id = data.get('device_id')
    
    print(f"[ACTIVATE] Key: {key}, Device: {device_id[:16]}..." if device_id else "[ACTIVATE] No device_id")
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    if not device_id:
        return jsonify({"success": False, "message": "Parameter 'device_id' required"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    
    # Cek expired
    if is_expired(key_info['exp']):
        return jsonify({
            "success": False, 
            "message": f"Key sudah expired pada {key_info['exp']}"
        }), 403
    
    # CEK BINDING DEVICE
    bound_device = key_info.get('bound_device')
    
    if bound_device:
        # Key sudah terikat ke device lain
        if bound_device != device_id:
            return jsonify({
                "success": False, 
                "message": "Key sudah terdaftar di device lain! Tidak bisa digunakan di device ini.",
                "bound_device": bound_device[:16] + "..." if len(bound_device) > 16 else bound_device
            }), 403
        else:
            # Device sama, validasi sukses
            return jsonify({
                "success": True,
                "message": "Key valid",
                "data": {
                    "name": key_info['name'],
                    "exp": key_info['exp'],
                    "bound_device": bound_device[:16] + "..." if len(bound_device) > 16 else bound_device
                }
            })
    else:
        # Key belum terikat - LAKUKAN BINDING
        DATABASE[key]['bound_device'] = device_id
        DATABASE[key]['activated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[BIND] Key '{key}' berhasil diikat ke device '{device_id[:16]}...'")
        
        return jsonify({
            "success": True,
            "message": "Aktivasi berhasil! Key terikat ke device ini.",
            "data": {
                "name": key_info['name'],
                "exp": key_info['exp'],
                "bound_device": device_id[:16] + "..."
            }
        })

@app.route('/check', methods=['GET'])  # <-- ENDPOINT LAMA (MASIH BISA DIPAKAI)
def check_key():
    """Endpoint lama untuk cek key tanpa binding (opsional)"""
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
    
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
    if not DATABASE:
        return jsonify({"success": True, "message": "Belum ada key yang terdaftar", "data": {}})
    
    # Tampilkan info key (tanpa bound_device full untuk keamanan)
    safe_data = {}
    for k, v in DATABASE.items():
        safe_data[k] = {
            "name": v['name'],
            "exp": v['exp'],
            "created_at": v.get('created_at'),
            "bound_device": v.get('bound_device')[:16] + "..." if v.get('bound_device') else None,
            "activated_at": v.get('activated_at')
        }
    
    return jsonify({
        "success": True, 
        "total_keys": len(DATABASE),
        "data": safe_data
    })

@app.route('/delete', methods=['GET'])
def delete_key():
    key = request.args.get('key')
    admin_key = request.args.get('admin', '')
    
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
        "data": {"name": deleted_data['name'], "exp": deleted_data['exp']}
    })

@app.route('/reset_device', methods=['POST'])  # <-- ENDPOINT RESET BINDING (UNTUK ADMIN)
def reset_device_binding():
    """Reset binding device dari suatu key (untuk kasus factory reset dll)"""
    admin_key = request.args.get('admin', '')
    data = request.get_json() or {}
    key = data.get('key')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    old_device = DATABASE[key].get('bound_device')
    DATABASE[key]['bound_device'] = None
    DATABASE[key]['activated_at'] = None
    
    print(f"[RESET] Key '{key}' binding direset. Old device: {old_device[:16] if old_device else 'None'}...")
    
    return jsonify({
        "success": True,
        "message": f"Binding device untuk key '{key}' berhasil direset",
        "old_device": old_device[:16] + "..." if old_device else None
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

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY (DENGAN DEVICE BINDING)")
    print("="*50)
    print(f"Total keys: {len(DATABASE)}")
    for key, info in DATABASE.items():
        status = "EXPIRED" if is_expired(info['exp']) else "VALID"
        bound = f"🔒 {info['bound_device'][:16]}..." if info.get('bound_device') else "🔓 UNBOUND"
        print(f"  {key} -> {info['name']} (exp: {info['exp']}) [{status}] | {bound}")
    print("="*50)
    print("Endpoint baru:")
    print("  POST /activate - untuk aktivasi dengan binding device")
    print("  POST /reset_device?admin=admin123 - reset binding")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
