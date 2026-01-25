import psycopg2
import os

# Database connection
conn = psycopg2.connect(
    dbname="securesync",
    user="securesync_user",
    password=os.getenv("DB_PASSWORD", "password"),
    host="localhost"
)
conn.autocommit = True
cur = conn.cursor()

# --------- WHITELIST ---------

def is_ip_whitelisted(ip):
    """Check if IP is in whitelist"""
    cur.execute("SELECT 1 FROM whitelist_ips WHERE ip=%s", (ip,))
    return cur.fetchone() is not None

def add_ip_to_whitelist(ip):
    """Add IP to whitelist"""
    try:
        cur.execute("INSERT INTO whitelist_ips (ip) VALUES (%s)", (ip,))
        return True
    except:
        return False

def remove_ip_from_whitelist(ip):
    """Remove IP from whitelist"""
    cur.execute("DELETE FROM whitelist_ips WHERE ip=%s", (ip,))
    return cur.rowcount > 0

def get_whitelisted_ips():
    """Get all whitelisted IPs"""
    cur.execute("SELECT ip, added_at FROM whitelist_ips ORDER BY added_at DESC")
    return cur.fetchall()

# --------- PLANTS ---------

def get_plant(plant_id):
    """Get plant credentials"""
    cur.execute(
        "SELECT api_key FROM plants WHERE plant_id=%s",
        (plant_id,)
    )
    return cur.fetchone()

def add_plant(plant_id, api_key):
    """Add new plant"""
    try:
        cur.execute(
            "INSERT INTO plants (plant_id, api_key) VALUES (%s, %s)",
            (plant_id, api_key)
        )
        return True
    except:
        return False

def remove_plant(plant_id):
    """Remove plant"""
    cur.execute("DELETE FROM plants WHERE plant_id=%s", (plant_id,))
    return cur.rowcount > 0

# --------- REPLAY PROTECTION ---------

def is_nonce_used(nonce):
    """Check if nonce has been used before"""
    cur.execute(
        "SELECT 1 FROM replay_nonces WHERE nonce=%s",
        (nonce,)
    )
    return cur.fetchone() is not None

def store_nonce(nonce):
    """Store nonce to prevent replay attacks"""
    cur.execute(
        "INSERT INTO replay_nonces (nonce) VALUES (%s)",
        (nonce,)
    )

def cleanup_old_nonces(age_seconds=300):
    """Clean up nonces older than specified age"""
    cur.execute("""
        DELETE FROM replay_nonces 
        WHERE created_at < NOW() - INTERVAL '%s seconds'
    """, (age_seconds,))
    return cur.rowcount

# --------- AUDIT LOG ---------

def log_audit(plant_id, payload_hash, source_ip):
    """Log successful data sync"""
    cur.execute("""
        INSERT INTO audit_logs (plant_id, payload_hash, source_ip)
        VALUES (%s, %s, %s)
    """, (plant_id, payload_hash, source_ip))

# --------- ATTACK LOG ---------

def log_attack(source_ip, plant_id, attack_type, reason):
    """Log security attack/violation"""
    cur.execute("""
        INSERT INTO attack_logs (source_ip, plant_id, attack_type, reason)
        VALUES (%s, %s, %s, %s)
    """, (source_ip, plant_id, attack_type, reason))

def get_failed_attempts(source_ip, minutes=5):
    """Get number of failed attempts from IP in last N minutes"""
    cur.execute("""
        SELECT COUNT(*) FROM attack_logs
        WHERE source_ip = %s
        AND created_at > NOW() - INTERVAL '%s minutes'
    """, (source_ip, minutes))
    result = cur.fetchone()
    return result[0] if result else 0

def cleanup_old_logs(days=30):
    """Clean up old logs"""
    cur.execute("""
        DELETE FROM attack_logs 
        WHERE created_at < NOW() - INTERVAL '%s days'
    """, (days,))
    attack_deleted = cur.rowcount
    
    cur.execute("""
        DELETE FROM audit_logs 
        WHERE created_at < NOW() - INTERVAL '%s days'
    """, (days,))
    audit_deleted = cur.rowcount
    
    return {"attack_logs": attack_deleted, "audit_logs": audit_deleted}
