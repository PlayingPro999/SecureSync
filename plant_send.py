import requests, base64, os, time, uuid
from crypto import load_or_create_rsa, aes_encrypt, rsa_encrypt, sign

URL = "http://127.0.0.1:8000/sync"
PLANT_ID = "PLANT_A"
API_KEY = "abc123"

# Load plant's private key and server's public key
plant_priv, _ = load_or_create_rsa("plant_a")
_, server_pub = load_or_create_rsa("server")

# Original payload
payload = b"production=1200;temp=71"

# 1. Generate random AES key
aes_key = os.urandom(32)

# 2. Encrypt payload with AES
nonce, cipher = aes_encrypt(aes_key, payload)

# 3. Encrypt AES key with server's public RSA key
enc_key = rsa_encrypt(server_pub, aes_key)

# 4. Sign the plaintext payload with plant's private key
sig = sign(plant_priv, payload)

# 5. Prepare request data
data = {
    "plant_id": PLANT_ID,
    "api_key": API_KEY,
    "nonce_id": str(uuid.uuid4()),
    "timestamp": int(time.time()),
    "encrypted_key": base64.b64encode(enc_key).decode(),
    "cipher": base64.b64encode(cipher).decode(),
    "nonce": base64.b64encode(nonce).decode(),
    "signature": sig.hex()
}

# 6. Send request
try:
    r = requests.post(URL, json=data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
