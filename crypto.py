from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

KEY_DIR = "keys"
os.makedirs(KEY_DIR, exist_ok=True)

def load_or_create_rsa(name):
    priv_path = f"{KEY_DIR}/{name}_priv.pem"
    pub_path = f"{KEY_DIR}/{name}_pub.pem"

    if os.path.exists(priv_path):
        with open(priv_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, "rb") as f:
            pub = serialization.load_pem_public_key(f.read())
        return priv, pub

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()

    with open(priv_path, "wb") as f:
        f.write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(pub_path, "wb") as f:
        f.write(pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    return priv, pub

def aes_encrypt(key, data):
    aes = AESGCM(key)
    nonce = os.urandom(12)
    cipher = aes.encrypt(nonce, data, None)
    return nonce, cipher

def aes_decrypt(key, nonce, ciphertext):
    """Decrypt AES-GCM encrypted data"""
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)

def rsa_encrypt(pub, key):
    return pub.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def rsa_decrypt(priv, encrypted_key):
    """Decrypt RSA-encrypted AES key"""
    return priv.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def sign(priv, data):
    return priv.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

def verify_signature(plant_id, payload, signature):
    """Verify signature against plaintext payload"""
    _, pub = load_or_create_rsa(plant_id.lower())
    try:
        pub.verify(
            bytes.fromhex(signature) if isinstance(signature, str) else signature,
            payload if isinstance(payload, bytes) else payload.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False
