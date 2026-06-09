import warnings
warnings.filterwarnings('ignore')

import requests
import random
import string
import time
import json
import codecs
import base64
from datetime import datetime
from flask import Flask, request, jsonify
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ============ KONFIGURASI TELEGRAM ============
BOT_TOKEN = "8965307683:AAGXwuIge4QKuYXtrkXhG4AahxDrynqi7SY"
OWNER_ID = 8660700322
CHANNEL_PROMO = "@dindingijo"
CONTACT = "@ricaricahamstee"
WATERMARK = f"CH TELE {CHANNEL_PROMO} Join pls"

# ============ KONFIGURASI API KEYS ============
API_KEYS = {
    "FREE_KEY_001": {"limit": 50, "used": 0, "last_reset_day": 0},
    "VIP_KEY_001": {"limit": 500, "used": 0, "last_reset_day": 0},
    "UNLIMITED_001": {"limit": 999999, "used": 0, "last_reset_day": 0}
}

# ============ KONFIGURASI GENERATOR ============
REGION_CHOICE = 1

REGION_MAP = {
    1: {"code": "ID", "name": "INDONESIA", "lang": "id"},
    2: {"code": "ME", "name": "MIDDLE EAST", "lang": "ar"},
    3: {"code": "IND", "name": "INDIA", "lang": "hi"},
    4: {"code": "TH", "name": "THAILAND", "lang": "th"},
    5: {"code": "VN", "name": "VIETNAM", "lang": "vi"},
    6: {"code": "BD", "name": "BANGLADESH", "lang": "bn"},
    7: {"code": "PK", "name": "PAKISTAN", "lang": "ur"},
    8: {"code": "TW", "name": "TAIWAN", "lang": "zh"},
    9: {"code": "CIS", "name": "RUSSIA", "lang": "ru"},
    10: {"code": "SAC", "name": "SPAIN", "lang": "es"},
    11: {"code": "BR", "name": "BRAZIL", "lang": "pt"}
}

SELECTED = REGION_MAP.get(REGION_CHOICE, REGION_MAP[1])
REGION = SELECTED["code"]
REGION_NAME = SELECTED["name"]

NAME_PREFIX = "shuoi-"
PASS_PREFIX = "shu"
HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")

# ============ DEVICE POOL ============
DEVICE_POOL = []
samsung = [f"SM-{c}{random.randint(100,999)}" for _ in range(100) for c in "AGNFMSJE"]
xiaomi = [f"{p} {random.randint(7,14)}" for _ in range(80) for p in ["Redmi Note", "Redmi", "Poco F", "Poco X", "Mi", "Xiaomi"]]
oppo = [f"OPPO {m}{random.randint(2,9999)}" for _ in range(60) for m in ["CPH", "Find X", "Reno", "A", "F"]]
vivo = [f"vivo {m}{random.randint(1,9999)}" for _ in range(60) for m in ["V", "X", "Y", "T", "S"]]
realme = [f"Realme {m}{random.randint(7,70)}" for _ in range(50) for m in ["", " Pro", " GT ", " C", " Narzo "]]
oneplus = [f"OnePlus {random.randint(8,14)}" for _ in range(40)]
moto = [f"Moto {m}{random.randint(10,100)}" for _ in range(40) for m in ["G", "E", "Edge "]]
other = ["ASUS_I005DA","ASUS Zenfone 8","Google Pixel 6","Sony Xperia 1 III"] * 20
all_models = samsung + xiaomi + oppo + vivo + realme + oneplus + moto + other
brands = ["samsung","xiaomi","oppo","vivo","realme","oneplus","motorola","asus","google","sony"]
android_versions = ["9","10","11","12","13","14","15"]

for _ in range(2000):
    DEVICE_POOL.append({
        "model": random.choice(all_models),
        "brand": random.choice(brands),
        "android": random.choice(android_versions)
    })

# ============ TELEGRAM FUNCTION ============
def send_to_owner(account_id, uid, password, region_name, api_key, caller_ip):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"""🔥 <b>NEW ACCOUNT GENERATED VIA API</b> 🔥

🆔 Account ID: <code>{account_id}</code>
📝 UID: <code>{uid}</code>
🔑 <b>PASSWORD: <code>{password}</code></b>
🌍 Region: {region_name}
🔑 API Key: <code>{api_key}</code>
📞 IP Caller: {caller_ip}
⏰ Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}

💡 Join: {CHANNEL_PROMO}"""
    
    payload = {
        "chat_id": OWNER_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ============ GENERATOR FUNCTIONS ============
def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def get_headers():
    device = random.choice(DEVICE_POOL)
    return {
        "User-Agent": f"GarenaMSDK/4.0.39({device['model']};Android {device['android']};en;ID;)",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": f"v1 {random.randint(100000, 999999)}",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
    }

def get_headers_form():
    h = get_headers()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

def encode_varint(n):
    if n < 0: return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n: byte |= 0x80
        result.append(byte)
        if not n: break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, dict):
        nested = b''
        for k, v in value.items():
            nested += create_proto_field(k, v)
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(nested)) + nested
    elif isinstance(value, int):
        header = (field_num << 3) | 0
        return encode_varint(header) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def aes_encrypt(hex_data):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    data = bytes.fromhex(hex_data)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    plain = bytes.fromhex(plain_hex)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

def generate_cool_name():
    base = f"{NAME_PREFIX}{random.randint(10, 999)}"
    syms = ['~','!','@','#','$','%','^','&','*','-','_','+','=']
    p = random.randint(1, 3)
    if p == 1:
        s = random.choice(syms)
        return f"{s}{base}{s}"
    elif p == 2:
        s1, s2 = random.sample(syms, 2)
        return f"{s1}{s2}{base}"
    else:
        return base

def major_login(uid, password, access_token, open_id, region):
    try:
        lang = "id" if region == "ID" else "en"
        payload_parts = [
            b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
            lang.encode("ascii"),
            b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        ]
        payload = b''.join(payload_parts)
        
        if region in ["ME", "TH"]:
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
        else:
            url = "https://loginbp.ggblueshark.com/MajorLogin"
        
        headers = {
            "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
            "Host": "loginbp.ggblueshark.com" if region not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
            "ReleaseVersion": "OB53", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
            "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
        }
        
        data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
        data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        d = encrypt_api(data.hex())
        
        session = requests.Session()
        session.verify = False
        response = session.post(url, headers=headers, data=bytes.fromhex(d), timeout=15)
        
        if response.status_code == 200 and len(response.text) > 10:
            jwt_start = response.text.find("eyJ")
            if jwt_start != -1:
                jwt_token = response.text[jwt_start:]
                second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
                if second_dot != -1:
                    jwt_token = jwt_token[:second_dot + 44]
                try:
                    parts = jwt_token.split('.')
                    if len(parts) >= 2:
                        payload_part = parts[1]
                        padding = 4 - len(payload_part) % 4
                        if padding != 4: 
                            payload_part += '=' * padding
                        decoded = base64.urlsafe_b64decode(payload_part)
                        data = json.loads(decoded)
                        account_id = data.get('account_id') or data.get('external_id')
                        if account_id:
                            return {"account_id": str(account_id), "jwt_token": jwt_token}
                except:
                    pass
        return {"account_id": "N/A", "jwt_token": ""}
    except:
        return {"account_id": "N/A", "jwt_token": ""}

def generate_one_account():
    session = requests.Session()
    session.verify = False
    
    for retry in range(2):
        try:
            password = f"{PASS_PREFIX}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
            name = generate_cool_name()
            
            resp = session.post(
                "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                headers=get_headers(),
                json={"app_id": 100067, "client_type": 2, "password": password, "source": 2},
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and "uid" in data["data"]:
                    uid = data["data"]["uid"]
                    
                    time.sleep(0.03)
                    
                    resp2 = session.post(
                        "https://100067.connect.garena.com/oauth/guest/token/grant",
                        headers=get_headers_form(),
                        data={"uid": uid, "password": password, "response_type": "token", "client_type": "2", "client_secret": HEX_KEY, "client_id": "100067"},
                        timeout=15
                    )
                    
                    if resp2.status_code == 200:
                        token_data = resp2.json()
                        open_id = token_data.get('open_id', '')
                        access_token = token_data.get('access_token', '')
                        
                        if open_id and access_token:
                            keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
                            encoded = ""
                            for i in range(len(open_id)):
                                encoded += chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
                            hex_str = ''.join(c if 32 <= ord(c) <= 126 else '\\u{:04x}'.format(ord(c)) for c in encoded)
                            field = codecs.decode(hex_str, 'unicode_escape').encode('latin1')
                            
                            if REGION in ["ME", "TH"]:
                                url_major = "https://loginbp.common.ggbluefox.com/MajorRegister"
                            else:
                                url_major = "https://loginbp.ggblueshark.com/MajorRegister"
                            
                            lang_code = "id" if REGION == "ID" else "en"
                            payload = {1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field, 15: lang_code, 16: 1, 17: 1}
                            payload_bytes = build_proto(payload)
                            encrypted_payload = aes_encrypt(payload_bytes.hex())
                            
                            headers_major = {
                                "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
                                "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
                                "Host": "loginbp.ggblueshark.com" if REGION not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
                                "ReleaseVersion": "OB53", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
                                "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
                            }
                            
                            session.post(url_major, headers=headers_major, data=encrypted_payload, timeout=15)
                            
                            time.sleep(0.03)
                            
                            login_result = major_login(uid, password, access_token, open_id, REGION)
                            account_id = login_result.get("account_id", "N/A")
                            
                            if account_id != "N/A":
                                return {
                                    "account_id": account_id,
                                    "uid": uid,
                                    "password": password,
                                    "region": REGION_NAME,
                                    "region_code": REGION
                                }
        except:
            pass
        
        time.sleep(0.5)
    
    return None

# ============ API KEY FUNCTIONS ============
def check_api_key(api_key):
    current_day = datetime.now().day
    
    if api_key not in API_KEYS:
        return False, "Invalid API key", None
    
    key_data = API_KEYS[api_key]
    
    if key_data.get("last_reset_day", 0) != current_day:
        key_data["used"] = 0
        key_data["last_reset_day"] = current_day
    
    if key_data["used"] >= key_data["limit"]:
        return False, f"Daily limit reached! Used {key_data['used']}/{key_data['limit']}", key_data
    
    return True, "OK", key_data

def update_api_key_usage(api_key):
    if api_key in API_KEYS:
        API_KEYS[api_key]["used"] += 1

# ============ FLASK ROUTES ============
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({
        "success": True,
        "message": "API is running!",
        "endpoints": {
            "/generate": "Generate account (GET/POST with key parameter)",
            "/status": "Check API key status"
        },
        "watermark": WATERMARK
    })

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    api_key = None
    
    if request.method == 'GET':
        api_key = request.args.get('key') or request.args.get('api_key')
    else:
        api_key = request.json.get('key') if request.is_json else request.form.get('key')
    
    if not api_key:
        return jsonify({
            "success": False,
            "error": "API_KEY_REQUIRED",
            "message": "API key required! Use ?key=YOUR_KEY",
            "available_keys": list(API_KEYS.keys()),
            "example": "/generate?key=FREE_KEY_001",
            "watermark": WATERMARK
        }), 401
    
    valid, msg, key_data = check_api_key(api_key)
    
    if not valid:
        return jsonify({
            "success": False,
            "error": "LIMIT_REACHED",
            "message": msg,
            "limit": key_data.get("limit", 0) if key_data else 0,
            "used": key_data.get("used", 0) if key_data else 0,
            "remaining": max(0, key_data.get("limit", 0) - key_data.get("used", 0)) if key_data else 0,
            "watermark": WATERMARK
        }), 429
    
    try:
        result = generate_one_account()
        
        if result:
            update_api_key_usage(api_key)
            remaining = API_KEYS[api_key]["limit"] - API_KEYS[api_key]["used"]
            
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            send_to_owner(
                result["account_id"],
                result["uid"],
                result["password"],
                result["region"],
                api_key,
                client_ip
            )
            
            # UNTUK UNLIMITED_001: KASIH PASSWORD
            # UNTUK KEY LAIN: TANPA PASSWORD
            if api_key == "UNLIMITED_001":
                return jsonify({
                    "success": True,
                    "message": "Account generated successfully!",
                    "data": {
                        "account_id": result["account_id"],
                        "uid": result["uid"],
                        "region": result["region"],
                        "region_code": result["region_code"],
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "password": result["password"],
                    "usage": {
                        "used": API_KEYS[api_key]["used"],
                        "limit": API_KEYS[api_key]["limit"],
                        "remaining": remaining
                    },
                    "watermark": WATERMARK
                })
            else:
                return jsonify({
                    "success": True,
                    "message": "Account generated successfully!",
                    "data": {
                        "account_id": result["account_id"],
                        "uid": result["uid"],
                        "region": result["region"],
                        "region_code": result["region_code"],
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "note": f"maaf ya ak ga ikutin password nya, klo mau chat aja {CONTACT}",
                    "usage": {
                        "used": API_KEYS[api_key]["used"],
                        "limit": API_KEYS[api_key]["limit"],
                        "remaining": remaining
                    },
                    "watermark": WATERMARK
                })
        else:
            return jsonify({
                "success": False,
                "error": "GENERATION_FAILED",
                "message": "Failed to generate account. Please try again.",
                "watermark": WATERMARK
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": str(e),
            "watermark": WATERMARK
        }), 500

@app.route('/status', methods=['GET'])
def status():
    api_key = request.args.get('key') or request.args.get('api_key')
    
    if not api_key:
        return jsonify({
            "success": False,
            "message": "API key required",
            "watermark": WATERMARK
        }), 401
    
    valid, msg, key_data = check_api_key(api_key)
    
    if not valid or not key_data:
        return jsonify({
            "success": False,
            "message": msg,
            "watermark": WATERMARK
        }), 404
    
    return jsonify({
        "success": True,
        "api_key": api_key,
        "limit": key_data["limit"],
        "used": key_data["used"],
        "remaining": key_data["limit"] - key_data["used"],
        "reset_daily": True,
        "watermark": WATERMARK
    })

if __name__ == '__main__':
    app.run(debug=True)
