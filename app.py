from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import os
import threading
import time

app = Flask(__name__)

DB_FILE = "database.json"
DATABASE = {}

# ==================== FUNGSI DATABASE ====================
def load_database():
    global DATABASE
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            DATABASE = json.load(f)
        print(f"✅ Loaded: {len(DATABASE)} keys")
    else:
        DATABASE = {}
        print("✅ Database baru")

def save_database():
    with open(DB_FILE, 'w') as f:
        json.dump(DATABASE, f, indent=4)

def check_expired_keys():
    while True:
        now = datetime.now()
        expired_keys = []
        for key, info in DATABASE.items():
            exp_date = datetime.strptime(info['exp'], "%Y-%m-%d")
            if now.date() > exp_date.date():
                expired_keys.append(key)
        
        for key in expired_keys:
            del DATABASE[key]
            print(f"🗑️ Expired: {key}")
        
        if expired_keys:
            save_database()
        time.sleep(60)

load_database()
threading.Thread(target=check_expired_keys, daemon=True).start()

# ==================== HALAMAN WEB (KLIK-KLIK) ====================
html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>API Key Manager - Simple</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #aaa; }
        
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .card h2 {
            color: white;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .input-group input {
            flex: 1;
            padding: 12px 15px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 1em;
        }
        .input-group input::placeholder {
            color: rgba(255,255,255,0.5);
        }
        .input-group select {
            padding: 12px 15px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 1em;
            cursor: pointer;
        }
        .input-group select option {
            background: #1a1a2e;
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102,126,234,0.4);
        }
        .btn-danger {
            background: #dc2626;
            color: white;
        }
        .btn-danger:hover {
            background: #b91c1c;
        }
        .btn-success {
            background: #10b981;
            color: white;
        }
        
        .result {
            background: rgba(0,0,0,0.5);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #10b981;
            word-break: break-all;
            max-height: 200px;
            overflow: auto;
        }
        
        .key-list {
            margin-top: 15px;
        }
        .key-item {
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .key-info {
            color: white;
            font-family: monospace;
        }
        .key-status {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8em;
        }
        .status-valid {
            background: #10b981;
            color: white;
        }
        .key-actions {
            display: flex;
            gap: 8px;
        }
        .btn-small {
            padding: 6px 12px;
            font-size: 0.8em;
        }
        
        .note {
            background: rgba(245, 158, 11, 0.2);
            border-left: 3px solid #f59e0b;
            padding: 15px;
            border-radius: 10px;
            color: #fcd34d;
            margin-top: 15px;
        }
        hr {
            border-color: rgba(255,255,255,0.1);
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 API Key Manager</h1>
            <p>Buat & Kelola Key untuk scgen.py | Auto-delete expired key</p>
        </div>
        
        <!-- CREATE KEY -->
        <div class="card">
            <h2>📝 Buat Key Baru</h2>
            <div class="input-group">
                <input type="text" id="keyName" placeholder="Nama Key (contoh: mykey123)">
                <select id="expDays">
                    <option value="1">1 hari (untuk scgen)</option>
                    <option value="3">3 hari</option>
                    <option value="7">7 hari</option>
                    <option value="14">14 hari</option>
                    <option value="30" selected>30 hari (default)</option>
                    <option value="60">60 hari</option>
                    <option value="90">90 hari</option>
                </select>
                <input type="text" id="ownerName" placeholder="Nama Owner (opsional)" value="Premium User">
            </div>
            <button class="btn-primary" onclick="generateKey()">✨ Generate Key</button>
            <div id="generateResult" class="result" style="display:none"></div>
        </div>
        
        <!-- QUICK CHECK -->
        <div class="card">
            <h2>🔍 Cek Key</h2>
            <div class="input-group">
                <input type="text" id="checkKey" placeholder="Masukkan key untuk dicek">
                <button class="btn-primary" onclick="checkKey()">Cek Validitas</button>
            </div>
            <div id="checkResult" class="result" style="display:none"></div>
        </div>
        
        <!-- LIST ALL KEYS -->
        <div class="card">
            <h2>📋 Daftar Semua Key</h2>
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <button class="btn-primary" onclick="listKeys()">🔄 Refresh</button>
                <button class="btn-danger" onclick="clearAll()" style="background:#dc2626">⚠️ Hapus Semua</button>
            </div>
            <div id="keyListContainer" class="key-list">
                <div style="color:#aaa; text-align:center">Klik Refresh untuk melihat key</div>
            </div>
        </div>
        
        <!-- INFO -->
        <div class="card">
            <h2>ℹ️ Informasi</h2>
            <div class="note">
                <strong>✅ scgen.py FULL COMPATIBLE!</strong><br>
                • Key yang dibuat di sini LANGSUNG bisa dipakai di scgen<br>
                • scgen akan otomatis validasi key via API ini<br>
                • Key expired otomatis dihapus setiap 60 detik<br>
                • Cukup copy-paste key ke scgen saat activation
            </div>
            <hr>
            <div style="color:#aaa; font-size:0.85em">
                <strong>📌 Cara pakai di scgen:</strong><br>
                1. Buat key di sini (contoh: <code>mykey123</code>)<br>
                2. Jalankan scgen.py<br>
                3. Masukkan key <code>mykey123</code> saat activation<br>
                4. Selesai! scgen akan bekerja normal ✅
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = window.location.origin;
        
        async function generateKey() {
            const key = document.getElementById('keyName').value.trim();
            const days = document.getElementById('expDays').value;
            const name = document.getElementById('ownerName').value.trim() || 'Premium User';
            
            if (!key) {
                alert('Masukkan nama key dulu!');
                return;
            }
            
            const resultDiv = document.getElementById('generateResult');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '⏳ Membuat key...';
            resultDiv.style.color = '#fbbf24';
            
            try {
                const response = await fetch(`${API_URL}/generate?key=${encodeURIComponent(key)}&exp=${days}&name=${encodeURIComponent(name)}`);
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ BERHASIL!<br>🔑 Key: <strong style="color:#10b981">${key}</strong><br>📅 Expired: ${data.data.exp}<br>👤 Owner: ${name}<br><br>📌 Copy key ini untuk scgen: <strong style="color:#fbbf24">${key}</strong>`;
                    resultDiv.style.color = '#10b981';
                    listKeys(); // Refresh list
                } else {
                    resultDiv.innerHTML = `❌ GAGAL: ${data.message}`;
                    resultDiv.style.color = '#ef4444';
                }
            } catch (err) {
                resultDiv.innerHTML = `❌ Error: ${err.message}`;
                resultDiv.style.color = '#ef4444';
            }
        }
        
        async function checkKey() {
            const key = document.getElementById('checkKey').value.trim();
            if (!key) {
                alert('Masukkan key yang ingin dicek!');
                return;
            }
            
            const resultDiv = document.getElementById('checkResult');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '⏳ Mengecek...';
            
            try {
                const response = await fetch(`${API_URL}/check?key=${encodeURIComponent(key)}`);
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ KEY VALID!<br>🔑 Key: ${key}<br>👤 Owner: ${data.data.name}<br>📅 Expired: ${data.data.exp}`;
                    resultDiv.style.color = '#10b981';
                } else {
                    resultDiv.innerHTML = `❌ ${data.message}`;
                    resultDiv.style.color = '#ef4444';
                }
            } catch (err) {
                resultDiv.innerHTML = `❌ Error: ${err.message}`;
            }
        }
        
        async function listKeys() {
            const container = document.getElementById('keyListContainer');
            container.innerHTML = '<div style="color:#aaa">⏳ Loading...</div>';
            
            try {
                const response = await fetch(`${API_URL}/listkey001`);
                const data = await response.json();
                
                if (data.success && data.total_keys > 0) {
                    let html = '';
                    for (const [key, info] of Object.entries(data.data)) {
                        const expDate = new Date(info.exp);
                        const now = new Date();
                        const isValid = expDate > now;
                        html += `
                            <div class="key-item">
                                <div>
                                    <div class="key-info">🔑 <strong>${key}</strong></div>
                                    <div style="font-size:0.8em; color:#aaa">👤 ${info.name} | 📅 Exp: ${info.exp}</div>
                                </div>
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <span class="key-status ${isValid ? 'status-valid' : ''}" style="${!isValid ? 'background:#ef4444;color:white' : ''}">
                                        ${isValid ? '✅ Valid' : '❌ Expired'}
                                    </span>
                                    <button class="btn-small" style="background:#ef4444" onclick="deleteKey('${key}')">🗑️</button>
                                </div>
                            </div>
                        `;
                    }
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<div style="color:#aaa; text-align:center">📭 Belum ada key. Buat key baru di atas!</div>';
                }
            } catch (err) {
                container.innerHTML = `<div style="color:#ef4444">❌ Error: ${err.message}</div>`;
            }
        }
        
        async function deleteKey(key) {
            if (!confirm(`Hapus key "${key}"?`)) return;
            
            try {
                const response = await fetch(`${API_URL}/delete?key=${encodeURIComponent(key)}`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    listKeys();
                } else {
                    alert(`Gagal: ${data.message}`);
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }
        
        async function clearAll() {
            if (!confirm('⚠️ PERINGATAN! Ini akan menghapus SEMUA key. Lanjutkan?')) return;
            
            try {
                const response = await fetch(`${API_URL}/clear-all`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    alert(`✅ ${data.message}`);
                    listKeys();
                    document.getElementById('generateResult').style.display = 'none';
                    document.getElementById('checkResult').style.display = 'none';
                } else {
                    alert(`Gagal: ${data.message}`);
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }
        
        // Auto refresh list setiap 10 detik
        setInterval(listKeys, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_page)

# ==================== ROUTE API (SAMA PERSIS DENGAN scgen EXPECTED) ====================
@app.route('/generate', methods=['GET'])
def generate_key():
    key = request.args.get('key')
    days_exp = int(request.args.get('exp', 30))
    name = request.args.get('name', 'Unknown')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key in DATABASE:
        return jsonify({"success": False, "message": "Key sudah ada"}), 409
    
    expiry_date = (datetime.now() + timedelta(days=days_exp)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "duration": f"{days_exp} hari"
    }
    
    save_database()
    
    return jsonify({
        "success": True,
        "message": "Key berhasil dibuat",
        "data": DATABASE[key]
    })

@app.route('/generate-24h', methods=['POST'])
def generate_24h_key():
    data = request.get_json()
    
    if not data or 'key' not in data:
        return jsonify({"success": False, "message": "Body JSON harus berisi 'key'"}), 400
    
    key = data['key']
    name = data.get('name', 'Unknown')
    
    if key in DATABASE:
        return jsonify({"success": False, "message": "Key sudah ada"}), 409
    
    expiry_date = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d')
    
    DATABASE[key] = {
        "name": name,
        "exp": expiry_date,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "duration": "24 jam"
    }
    
    save_database()
    
    return jsonify({
        "success": True,
        "message": "Key 24 jam berhasil dibuat",
        "data": DATABASE[key]
    })

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    key_info = DATABASE[key]
    now = datetime.now().date()
    exp_date = datetime.strptime(key_info['exp'], "%Y-%m-%d").date()
    
    if now > exp_date:
        del DATABASE[key]
        save_database()
        return jsonify({
            "success": False,
            "message": "Key sudah expired dan dihapus",
            "data": key_info
        }), 403
    
    return jsonify({
        "success": True,
        "message": "Key valid",
        "data": {
            "name": key_info.get("name", "Premium User"),
            "exp": key_info["exp"]
        }
    })

@app.route('/listkey001', methods=['GET'])
def list_keys():
    if not DATABASE:
        return jsonify({
            "success": True,
            "message": "Belum ada key",
            "total_keys": 0,
            "data": {}
        })
    
    return jsonify({
        "success": True,
        "total_keys": len(DATABASE),
        "data": DATABASE
    })

@app.route('/delete', methods=['DELETE'])
def delete_key():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' wajib diisi"}), 400
    
    if key not in DATABASE:
        return jsonify({"success": False, "message": "Key tidak ditemukan"}), 404
    
    deleted_data = DATABASE.pop(key)
    save_database()
    
    return jsonify({
        "success": True,
        "message": "Key berhasil dihapus",
        "data": deleted_data
    })

@app.route('/clear-all', methods=['DELETE'])
def clear_all():
    count = len(DATABASE)
    DATABASE.clear()
    save_database()
    
    return jsonify({
        "success": True,
        "message": f"Semua key ({count}) berhasil dihapus"
    })

# ==================== RUN ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🔑 API Key Manager - READY!")
    print("📍 Buka http://127.0.0.1:5000")
    print("✅ scgen.py FULL COMPATIBLE")
    print("📝 Key format: YYYY-MM-DD (scgen format)")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)
