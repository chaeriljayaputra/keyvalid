from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL API PHP yang sudah diupload ke InfinityFree
PHP_API_URL = "https://aurelstore.id/api.php"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "running",
        "message": "API Key Server (Proxy Mode)",
        "php_api": PHP_API_URL
    })

@app.route('/check', methods=['GET'])
def check_key():
    """Cek key - proxy ke PHP API"""
    key = request.args.get('key')
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    try:
        resp = requests.get(f"{PHP_API_URL}/check?key={key}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Cannot connect to PHP API. Check if aurelstore.id is accessible."}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/activate', methods=['POST'])
def activate_key():
    """Aktivasi key - proxy ke PHP API"""
    try:
        resp = requests.post(f"{PHP_API_URL}/activate", json=request.get_json(), timeout=30)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Cannot connect to PHP API"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/listkey001', methods=['GET'])
def list_keys():
    """List semua key - proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/listkey001?admin={admin}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Cannot connect to PHP API"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete', methods=['GET'])
def delete_key():
    """Hapus key - proxy ke PHP API"""
    admin = request.args.get('admin', '')
    key = request.args.get('key', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/delete?admin={admin}&key={key}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/generate', methods=['GET'])
def generate_key():
    """Generate key baru - proxy ke PHP API"""
    admin = request.args.get('admin', '')
    key = request.args.get('key', '')
    exp = request.args.get('exp', '30')
    name = request.args.get('name', 'Unknown')
    try:
        resp = requests.get(f"{PHP_API_URL}/generate?admin={admin}&key={key}&exp={exp}&name={name}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reset_device', methods=['POST'])
def reset_device():
    """Reset binding device - proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.post(f"{PHP_API_URL}/reset_device?admin={admin}", json=request.get_json(), timeout=30)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reset', methods=['GET'])
def reset_all():
    """Reset semua key - proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/reset?admin={admin}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
