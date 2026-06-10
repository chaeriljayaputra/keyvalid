from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os
import pymysql
import json

app = Flask(__name__)

# ============ KONFIGURASI DATABASE MYSQL (InfinityFree) ============
DB_CONFIG = {
    'host': 'sql206.infinityfree.com',
    'user': 'if0_41752502',
    'password': 'cpbE8wln8DxqpnA',
    'database': 'if0_41752502_aurelstore_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# ============ KONFIGURASI DEFAULT KEYS ============
DEFAULT_KEYS = {
    "MEMBERSENDI": {"name": "Trial User", "exp": "2025-12-31", "created_at": "2024-01-01"},
    "ARYA": {"name": "ARYA User", "exp": "2026-06-15", "created_at": "2024-01-01"},
    "YANZZZZ": {"name": "YANZ User", "exp": "2099-12-30", "created_at": "2024-01-01"},
    "YANZ": {"name": "Permanent User", "exp": "2099-12-31", "created_at": "2024-01-01"}
}
# =================================================

def get_db():
    return pymysql.connect(**DB_CONFIG)

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Buat tabel keys
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `keys` (
                `id` VARCHAR(50) PRIMARY KEY,
                `name` VARCHAR(100) NOT NULL,
                `exp` DATE NOT NULL,
                `created_at` DATE NOT NULL,
                `bound_device` VARCHAR(64) DEFAULT NULL,
                `activated_at` DATETIME DEFAULT NULL
            )
        ''')
        
        # Insert default keys jika belum ada
        for kid, kinfo in DEFAULT_KEYS.items():
            cursor.execute('''
                INSERT IGNORE INTO `keys` (id, name, exp, created_at)
                VALUES (%s, %s, %s, %s)
            ''', (kid, kinfo['name'], kinfo['exp'], kinfo['created_at']))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Database ready")
    except Exception as e:
        print(f"[DB] Init error: {e}")

def is_expired(exp_date):
    return datetime.now().strftime('%Y-%m-%d') > exp_date

# Inisialisasi database saat startup
init_db()

# ============ ROUTES ============

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "running",
        "message": "API Key Server Active",
        "endpoints": {
            "check": "/check?key=KEY",
            "activate": "POST /activate",
            "generate": "/generate?admin=admin123&key=KEY&exp=30&name=NAME",
            "list": "/listkey001?admin=admin123",
            "delete": "/delete?admin=admin123&key=KEY",
            "reset_device": "POST /reset_device?admin=admin123",
            "reset_all": "/reset?admin=admin123"
        }
    })

@app.route('/check', methods=['GET'])
def check_key():
    """Cek key tanpa binding - tetep pakai endpoint /check"""
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `keys` WHERE id = %s", (key,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not data:
            return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
        
        if is_expired(data['exp']):
            return jsonify({
                "success": False, 
                "message": f"Key sudah expired pada {data['exp']}"
            }), 403
        
        return jsonify({
            "success": True,
            "message": "Key valid",
            "data": {
                "name": data['name'],
                "exp": data['exp'].strftime('%Y-%m-%d') if hasattr(data['exp'], 'strftime') else data['exp']
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/activate', methods=['POST'])
def activate_key():
    """Aktivasi key dengan binding device"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400
    
    key = data.get('key')
    device_id = data.get('device_id')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    if not device_id:
        return jsonify({"success": False, "message": "Parameter 'device_id' required"}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM `keys` WHERE id = %s", (key,))
        key_data = cursor.fetchone()
        
        if not key_data:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
        
        if is_expired(key_data['exp']):
            cursor.close()
            conn.close()
            return jsonify({
                "success": False, 
                "message": f"Key sudah expired pada {key_data['exp']}"
            }), 403
        
        bound_device = key_data.get('bound_device')
        
        if bound_device:
            if bound_device != device_id:
                return jsonify({
                    "success": False,
                    "message": "Key sudah terdaftar di device lain! Tidak bisa digunakan.",
                    "bound_device": bound_device[:16] + "..." if len(bound_device) > 16 else bound_device
                }), 403
            else:
                cursor.close()
                conn.close()
                return jsonify({
                    "success": True,
                    "message": "Key valid",
                    "data": {
                        "name": key_data['name'],
                        "exp": key_data['exp'].strftime('%Y-%m-%d') if hasattr(key_data['exp'], 'strftime') else key_data['exp']
                    }
                })
        else:
            # Binding device
            cursor.execute('''
                UPDATE `keys` 
                SET bound_device = %s, activated_at = %s 
                WHERE id = %s
            ''', (device_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key))
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[BIND] Key '{key}' terikat ke device '{device_id[:16]}...'")
            
            return jsonify({
                "success": True,
                "message": "Aktivasi berhasil! Key terikat ke device ini.",
                "data": {
                    "name": key_data['name'],
                    "exp": key_data['exp'].strftime('%Y-%m-%d') if hasattr(key_data['exp'], 'strftime') else key_data['exp']
                }
            })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/generate', methods=['GET'])
def generate_key():
    """Generate key baru (admin only)"""
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    days_exp = request.args.get('exp')
    name = request.args.get('name', 'Unknown')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
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
    created_at = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Cek apakah key sudah ada
        cursor.execute("SELECT id FROM `keys` WHERE id = %s", (key,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": f"Key '{key}' sudah ada"}), 400
        
        cursor.execute('''
            INSERT INTO `keys` (id, name, exp, created_at)
            VALUES (%s, %s, %s, %s)
        ''', (key, name, expiry_date, created_at))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Key berhasil dibuat",
            "data": {
                "key": key,
                "name": name,
                "exp": expiry_date,
                "created_at": created_at
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/listkey001', methods=['GET'])
def list_keys():
    """List semua key (admin only)"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, exp, created_at, bound_device, activated_at FROM `keys`")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = {}
        for row in rows:
            result[row['id']] = {
                "name": row['name'],
                "exp": row['exp'].strftime('%Y-%m-%d') if hasattr(row['exp'], 'strftime') else row['exp'],
                "created_at": row['created_at'].strftime('%Y-%m-%d') if hasattr(row['created_at'], 'strftime') else row['created_at'],
                "bound_device": row['bound_device'][:16] + "..." if row['bound_device'] else None,
                "activated_at": row['activated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['activated_at'] else None,
                "status": "EXPIRED" if is_expired(row['exp']) else "ACTIVE"
            }
        
        return jsonify({
            "success": True, 
            "total_keys": len(result),
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete', methods=['GET'])
def delete_key():
    """Hapus key (admin only)"""
    admin_key = request.args.get('admin', '')
    key = request.args.get('key')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM `keys` WHERE id = %s", (key,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
        
        cursor.execute("DELETE FROM `keys` WHERE id = %s", (key,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Key '{key}' berhasil dihapus"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/remove', methods=['GET'])
def remove_key():
    """Alias untuk delete (admin only)"""
    return delete_key()

@app.route('/reset_device', methods=['POST'])
def reset_device_binding():
    """Reset binding device (admin only)"""
    admin_key = request.args.get('admin', '')
    data = request.get_json() or {}
    key = data.get('key')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT bound_device FROM `keys` WHERE id = %s", (key,))
        key_info = cursor.fetchone()
        
        if not key_info:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": f"Key '{key}' tidak ditemukan"}), 404
        
        old_device = key_info.get('bound_device')
        
        cursor.execute('''
            UPDATE `keys` 
            SET bound_device = NULL, activated_at = NULL 
            WHERE id = %s
        ''', (key,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Binding device untuk key '{key}' berhasil direset",
            "old_device": old_device[:16] + "..." if old_device else None
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reset', methods=['GET'])
def reset_all():
    """Reset semua key ke default (admin only)"""
    admin_key = request.args.get('admin', '')
    
    if admin_key != 'admin123':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Hapus semua key
        cursor.execute("DELETE FROM `keys`")
        
        # Insert default keys
        for kid, kinfo in DEFAULT_KEYS.items():
            cursor.execute('''
                INSERT INTO `keys` (id, name, exp, created_at)
                VALUES (%s, %s, %s, %s)
            ''', (kid, kinfo['name'], kinfo['exp'], kinfo['created_at']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Database direset, default keys dimuat ulang",
            "total_keys": len(DEFAULT_KEYS)
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    print("="*50)
    print("API KEY SERVER READY")
    print("="*50)
    print("Database: MySQL InfinityFree")
    print("")
    print("ENDPOINTS:")
    print("  GET  /check?key=KEY")
    print("  POST /activate")
    print("  GET  /generate?admin=admin123&key=KEY&exp=30&name=NAME")
    print("  GET  /listkey001?admin=admin123")
    print("  GET  /delete?admin=admin123&key=KEY")
    print("  GET  /remove?admin=admin123&key=KEY")
    print("  POST /reset_device?admin=admin123")
    print("  GET  /reset?admin=admin123")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=5000)
