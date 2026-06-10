from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL API PHP yang sudah diupload ke InfinityFree
PHP_API_URL = "https://if0-41752502.users.infinityfree.com/api.php"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "running",
        "message": "API Key Server (Proxy Mode)",
        "php_api": PHP_API_URL
    })

@app.route('/check', methods=['GET'])
def check_key():
    """Proxy ke PHP API"""
    key = request.args.get('key')
    if not key:
        return jsonify({"success": False, "message": "Parameter 'key' required"}), 400
    
    try:
        resp = requests.get(f"{PHP_API_URL}/check?key={key}", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/activate', methods=['POST'])
def activate_key():
    """Proxy ke PHP API"""
    try:
        resp = requests.post(f"{PHP_API_URL}/activate", json=request.get_json(), timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/listkey001', methods=['GET'])
def list_keys():
    """Proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/listkey001?admin={admin}", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete', methods=['GET'])
def delete_key():
    """Proxy ke PHP API"""
    admin = request.args.get('admin', '')
    key = request.args.get('key', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/delete?admin={admin}&key={key}", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/generate', methods=['GET'])
def generate_key():
    """Proxy ke PHP API"""
    admin = request.args.get('admin', '')
    key = request.args.get('key', '')
    exp = request.args.get('exp', '30')
    name = request.args.get('name', 'Unknown')
    try:
        resp = requests.get(f"{PHP_API_URL}/generate?admin={admin}&key={key}&exp={exp}&name={name}", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reset_device', methods=['POST'])
def reset_device():
    """Proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.post(f"{PHP_API_URL}/reset_device?admin={admin}", json=request.get_json(), timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reset', methods=['GET'])
def reset_all():
    """Proxy ke PHP API"""
    admin = request.args.get('admin', '')
    try:
        resp = requests.get(f"{PHP_API_URL}/reset?admin={admin}", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
