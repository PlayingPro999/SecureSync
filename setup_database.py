import psycopg2
import os

# Database connection
conn = psycopg2.connect(
    dbname="postgres",  # Connect to default database first
    user="securesync_user",
    password=os.getenv("DB_PASSWORD", "password"),
    host="localhost"
)
conn.autocommit = True
cur = conn.cursor()

print("Setting up SecureSync database...")

# Create database if it doesn't exist
try:
    cur.execute("CREATE DATABASE securesync")
    print("✓ Database 'securesync' created")
except psycopg2.errors.DuplicateDatabase:
    print("✓ Database 'securesync' already exists")

# Close and reconnect to the securesync database
cur.close()
conn.close()

conn = psycopg2.connect(
    dbname="securesync",
    user="securesync_user",
    password=os.getenv("DB_PASSWORD", "password"),
    host="localhost"
)
conn.autocommit = True
cur = conn.cursor()

# Create tables
print("\nCreating tables...")

cur.execute("""
CREATE TABLE IF NOT EXISTS whitelist_ips (
    ip VARCHAR(45) PRIMARY KEY,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Table 'whitelist_ips' created")

cur.execute("""
CREATE TABLE IF NOT EXISTS plants (
    plant_id VARCHAR(50) PRIMARY KEY,
    api_key VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Table 'plants' created")

cur.execute("""
CREATE TABLE IF NOT EXISTS replay_nonces (
    nonce VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Table 'replay_nonces' created")

cur.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    plant_id VARCHAR(50),
    payload_hash CHAR(64),
    source_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Table 'audit_logs' created")

cur.execute("""
CREATE TABLE IF NOT EXISTS attack_logs (
    id SERIAL PRIMARY KEY,
    source_ip VARCHAR(45),
    plant_id VARCHAR(50),
    attack_type VARCHAR(50) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Table 'attack_logs' created")

# Create indexes
print("\nCreating indexes...")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_attack_logs_time
ON attack_logs(created_at)
""")
print("✓ Index 'idx_attack_logs_time' created")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_attack_logs_type
ON attack_logs(attack_type)
""")
print("✓ Index 'idx_attack_logs_type' created")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_audit_logs_time
ON audit_logs(created_at)
""")
print("✓ Index 'idx_audit_logs_time' created")

# Insert sample data
print("\nInserting sample data...")

# Add localhost to whitelist
try:
    cur.execute("INSERT INTO whitelist_ips (ip) VALUES ('127.0.0.1')")
    print("✓ Added 127.0.0.1 to whitelist")
except:
    print("✓ 127.0.0.1 already in whitelist")

# Add sample plant
try:
    cur.execute("""
        INSERT INTO plants (plant_id, api_key) 
        VALUES ('PLANT_A', 'abc123')
    """)
    print("✓ Added PLANT_A with API key 'abc123'")
except:
    print("✓ PLANT_A already exists")

try:
    cur.execute("""
        INSERT INTO plants (plant_id, api_key) 
        VALUES ('PLANT_B', 'xyz789')
    """)
    print("✓ Added PLANT_B with API key 'xyz789'")
except:
    print("✓ PLANT_B already exists")

print("\n✅ Database setup complete!")
print("\nYou can now:")
print("1. Start the FastAPI server: uvicorn main:app --reload")
print("2. Test with: python plant_send.py")

cur.close()
conn.close()
