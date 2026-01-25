from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from database import *
from utils import rate_limited
from crypto import verify_signature, load_or_create_rsa, rsa_decrypt, aes_decrypt
from config import MAX_PAYLOAD_SIZE
import hashlib, time, base64
from security import security  # Added
import firebase_admin
from firebase_admin import credentials, auth

app = FastAPI(title="SecureSync")

# Added: Apply security middleware (IP whitelist + rate limit for all requests)
app.middleware("http")(security)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Added: Initialize Firebase for admin auth verification
cred = credentials.Certificate("firebase-adminsdk.json")  # Assume this file exists
firebase_admin.initialize_app(cred)

# Added: Dependency for admin auth
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Load server private key for decryption
server_priv, _ = load_or_create_rsa("server")

@app.post("/sync")
def sync(data: dict, request: Request):
    ip = request.client.host

    # --- STEP 1: RATE LIMITING (THE SHIELD) ---
    # We do this FIRST to protect the database from being 
    # crushed by 1000+ simultaneous connection requests.
    if rate_limited(ip):
        log_attack(ip, data.get("plant_id"), "RATE_LIMIT", "Too many requests")
        raise HTTPException(429, "Rate limited")

    # --- STEP 2: IP WHITELIST CHECK ---
    # Only hits the database if the request is within the rate limit.
    if not is_ip_whitelisted(ip):
        log_attack(ip, None, "UNAUTHORIZED_IP", "IP not whitelisted")
        raise HTTPException(403, "IP not allowed")

    # --- STEP 3: PLANT AUTHENTICATION ---
    plant = get_plant(data.get("plant_id"))
    if not plant or plant[0] != data.get("api_key"):
        log_attack(ip, data.get("plant_id"), "INVALID_API_KEY", "Bad credentials")
        raise HTTPException(401, "Invalid plant")

    # --- STEP 4: TIMESTAMP VALIDATION ---
    if abs(time.time() - data.get("timestamp", 0)) > 30:
        log_attack(ip, data["plant_id"], "STALE_REQUEST", "Timestamp drift")
        raise HTTPException(400, "Stale request")

    # --- STEP 5: REPLAY PROTECTION (ATOMIC) ---
    # Store nonce BEFORE decryption to avoid race conditions
    # Database will reject duplicates automatically
    try:
        store_nonce(data["nonce_id"])
    except Exception:
        # If insert fails, nonce already exists = replay attack
        log_attack(ip, data["plant_id"], "REPLAY_ATTACK", "Duplicate nonce")
        raise HTTPException(409, "Replay attack")

    try:
        # --- STEP 6: DECRYPTION ---
        encrypted_aes_key = base64.b64decode(data["encrypted_key"])
        cipher = base64.b64decode(data["cipher"])
        nonce = base64.b64decode(data["nonce"])
        
        # Check payload size
        if len(cipher) > MAX_PAYLOAD_SIZE:
            log_attack(ip, data["plant_id"], "PAYLOAD_TOO_LARGE", f"Size: {len(cipher)}")
            raise HTTPException(413, "Payload too large")
        
        # Decrypt AES key using server's private RSA key
        aes_key = rsa_decrypt(server_priv, encrypted_aes_key)
        
        # Decrypt payload using AES key
        plaintext = aes_decrypt(aes_key, nonce, cipher)
        
        # --- STEP 7: SIGNATURE VERIFICATION ---
        if not verify_signature(data["plant_id"], plaintext, data["signature"]):
            log_attack(ip, data["plant_id"], "INVALID_SIGNATURE", "Signature mismatch")
            raise HTTPException(401, "Invalid signature")
        
    except HTTPException:
        # Re-raise HTTP exceptions (signature verification failures, etc.)
        raise
    except Exception as e:
        log_attack(ip, data.get("plant_id"), "DECRYPTION_FAILED", str(e))
        raise HTTPException(400, f"Decryption/Verification failed: {str(e)}")

    # --- STEP 8: SUCCESS LOGGING ---
    payload_hash = hashlib.sha256(plaintext).hexdigest()
    log_audit(data["plant_id"], payload_hash, ip)

    return {
        "status": "accepted",
        "payload_hash": payload_hash,
        "received_at": int(time.time())
    }

# --- ADMIN & MONITORING ENDPOINTS ---

@app.get("/admin/attack-stats")
def attack_stats(interval: str = "minute", current_user: dict = Depends(get_current_user)):
    cur.execute("""
        SELECT date_trunc(%s, created_at) AS t, count(*)
        FROM attack_logs
        GROUP BY t
        ORDER BY t DESC
        LIMIT 100
    """, (interval,))
    return [{"time": str(row[0]), "count": row[1]} for row in cur.fetchall()]

@app.get("/admin/audit-logs")
def audit_logs(current_user: dict = Depends(get_current_user)):
    cur.execute("""
        SELECT plant_id, payload_hash, source_ip, created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 100
    """)
    return [
        {
            "plant_id": row[0],
            "payload_hash": row[1],
            "source_ip": row[2],
            "created_at": str(row[3])
        }
        for row in cur.fetchall()
    ]

@app.get("/admin/attack-logs")
def attack_logs(current_user: dict = Depends(get_current_user)):
    cur.execute("""
        SELECT source_ip, plant_id, attack_type, reason, created_at
        FROM attack_logs
        ORDER BY created_at DESC
        LIMIT 100
    """)
    return [
        {
            "source_ip": row[0],
            "plant_id": row[1],
            "attack_type": row[2],
            "reason": row[3],
            "created_at": str(row[4])
        }
        for row in cur.fetchall()
    ]

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": int(time.time())}

# Optional: To serve frontend from backend (single deployment)
# Build frontend: cd frontend && npm run build
# Then uncomment:
# from fastapi.staticfiles import StaticFiles
# from starlette.responses import FileResponse
# from pathlib import Path
#
# frontend_dist = Path(__file__).parent / "frontend" / "dist"
# app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
#
# @app.get("/{full_path:path}", response_class=FileResponse)
# async def serve_react_app(full_path: str):
#     if full_path.startswith("api/") or full_path.startswith("admin/") or full_path.startswith("sync") or full_path.startswith("health"):
#         raise HTTPException(404)
#     file_path = frontend_dist / full_path
#     if file_path.is_file():
#         return FileResponse(file_path)
#     return FileResponse(frontend_dist / "index.html")