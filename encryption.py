"""
Data Encryption Module
Handles encryption/decryption of sensitive data at rest and in transit
"""
import os
import base64
import json
import secrets
from typing import Optional, Union, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import hashlib
import logging

logger = logging.getLogger(__name__)


class FieldEncryption:
    """Field-level encryption for sensitive database fields"""
    
    def __init__(self, key: bytes = None):
        """Initialize with encryption key"""
        if key is None:
            # Derive key from environment or generate
            key = self._derive_key()
        self.fernet = Fernet(key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from environment"""
        from flask import current_app
        
        # Get master key from environment
        master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        if not master_key:
            # In development, generate a key (NOT for production)
            if os.environ.get('FLASK_ENV') == 'development':
                master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
                logger.warning("Using generated encryption key for development!")
            else:
                raise ValueError("ENCRYPTION_MASTER_KEY must be set in production")
        
        # Derive Fernet key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'jsrush_salt_v1',  # Fixed salt for deterministic derivation
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        encrypted = self.fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_value: str) -> Optional[str]:
        """Decrypt an encrypted value"""
        if encrypted_value is None:
            return None
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: Dict[str, Any], fields: list) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], fields: list) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.decrypt(result[field])
        return result


class AES256GCM:
    """AES-256-GCM encryption for large data"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            key = self._generate_key()
        self.key = key
        self.aesgcm = AESGCM(key)
    
    def _generate_key(self) -> bytes:
        """Generate AES-256 key"""
        from flask import current_app
        master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        if not master_key:
            if os.environ.get('FLASK_ENV') == 'development':
                return secrets.token_bytes(32)
            raise ValueError("ENCRYPTION_MASTER_KEY required")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'jsrush_aes_salt_v1',
            iterations=100000,
        )
        return kdf.derive(master_key.encode())
    
    def encrypt(self, plaintext: Union[str, bytes], associated_data: bytes = None) -> Dict[str, str]:
        """Encrypt data with AES-256-GCM"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, associated_data)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'nonce': base64.b64encode(nonce).decode(),
            'tag': ''  # GCM includes tag in ciphertext
        }
    
    def decrypt(self, encrypted_data: Dict[str, str], associated_data: bytes = None) -> bytes:
        """Decrypt AES-256-GCM encrypted data"""
        try:
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            nonce = base64.b64decode(encrypted_data['nonce'])
            return self.aesgcm.decrypt(nonce, ciphertext, associated_data)
        except Exception as e:
            logger.error(f"AES-GCM decryption failed: {e}")
            raise ValueError("Decryption failed")


class RSAEncryption:
    """RSA encryption for key exchange and digital signatures"""
    
    def __init__(self, private_key: rsa.RSAPrivateKey = None, public_key: rsa.RSAPublicKey = None):
        self.private_key = private_key
        self.public_key = public_key
    
    @classmethod
    def generate_key_pair(cls, key_size: int = 2048) -> tuple:
        """Generate RSA key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        public_key = private_key.public_key()
        return cls(private_key=private_key, public_key=public_key)
    
    def encrypt(self, plaintext: Union[str, bytes], public_key: rsa.RSAPublicKey = None) -> bytes:
        """Encrypt with RSA public key (OAEP padding)"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        key = public_key or self.public_key
        if not key:
            raise ValueError("No public key available")
        
        ciphertext = key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(ciphertext)
    
    def decrypt(self, ciphertext: Union[str, bytes], private_key: rsa.RSAPrivateKey = None) -> bytes:
        """Decrypt with RSA private key"""
        if isinstance(ciphertext, str):
            ciphertext = base64.b64decode(ciphertext)
        
        key = private_key or self.private_key
        if not key:
            raise ValueError("No private key available")
        
        plaintext = key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext
    
    def sign(self, data: Union[str, bytes], private_key: rsa.RSAPrivateKey = None) -> bytes:
        """Sign data with RSA private key (PSS padding)"""
        if isinstance(data, str):
            data = data.encode()
        
        key = private_key or self.private_key
        if not key:
            raise ValueError("No private key available")
        
        signature = key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature)
    
    def verify(self, data: Union[str, bytes], signature: bytes, public_key: rsa.RSAPublicKey = None) -> bool:
        """Verify RSA signature"""
        if isinstance(data, str):
            data = data.encode()
        if isinstance(signature, str):
            signature = base64.b64decode(signature)
        
        key = public_key or self.public_key
        if not key:
            raise ValueError("No public key available")
        
        try:
            key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def serialize_private_key(self, password: bytes = None) -> bytes:
        """Serialize private key to PEM format"""
        encryption = serialization.NoEncryption()
        if password:
            encryption = serialization.BestAvailableEncryption(password)
        
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
    
    def serialize_public_key(self) -> bytes:
        """Serialize public key to PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    @classmethod
    def load_private_key(cls, pem_data: bytes, password: bytes = None):
        """Load private key from PEM"""
        private_key = serialization.load_pem_private_key(pem_data, password=password)
        return cls(private_key=private_key)
    
    @classmethod
    def load_public_key(cls, pem_data: bytes):
        """Load public key from PEM"""
        public_key = serialization.load_pem_public_key(pem_data)
        return cls(public_key=public_key)


class TokenEncryption:
    """Encryption for JWT tokens and session data"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.environ.get('TOKEN_ENCRYPTION_KEY')
        if not self.secret_key:
            if os.environ.get('FLASK_ENV') == 'development':
                self.secret_key = secrets.token_hex(32)
            else:
                raise ValueError("TOKEN_ENCRYPTION_KEY required")
        
        # Derive Fernet key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'jsrush_token_salt',
            iterations=100000,
        )
        self.fernet = Fernet(base64.urlsafe_b64encode(
            PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'jsrush_token_salt',
                iterations=100000,
            ).derive(self.secret_key.encode())
        ))
    
    def encrypt_token(self, payload: Dict[str, Any]) -> str:
        """Encrypt token payload"""
        data = json.dumps(payload, separators=(',', ':')).encode()
        encrypted = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decrypt token payload"""
        try:
            encrypted = base64.urlsafe_b64decode(token.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            return None


class HashingUtils:
    """Secure hashing utilities"""
    
    @staticmethod
    def hash_password(password: str, rounds: int = 12) -> str:
        """Hash password with bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=rounds)).decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage (SHA-256)"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, key_hash: str) -> bool:
        """Verify API key against hash"""
        return hmac.compare_digest(HashingUtils.hash_api_key(api_key), key_hash)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key(prefix: str = "nr") -> str:
        """Generate API key with prefix"""
        return f"{prefix}_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def constant_time_compare(val1: str, val2: str) -> bool:
        """Constant-time string comparison"""
        return hmac.compare_digest(val1, val2)
    
    @staticmethod
    def pbkdf2_hash(password: str, salt: bytes = None, iterations: int = 100000) -> tuple:
        """PBKDF2 hash with salt"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(password.encode())).decode()
        return key, base64.b64encode(salt).decode()
    
    @staticmethod
    def verify_pbkdf2(password: str, key: str, salt_b64: str, iterations: int = 100000) -> bool:
        """Verify PBKDF2 hash"""
        salt = base64.b64decode(salt_b64)
        derived_key, _ = HashingUtils.pbkdf2_hash(password, salt, iterations)
        return hmac.compare_digest(key, derived_key)


class SecureStorage:
    """Secure storage for sensitive configuration"""
    
    def __init__(self, encryption_key: bytes = None):
        self.field_encryption = FieldEncryption(encryption_key)
    
    def store_secret(self, key: str, value: str) -> str:
        """Encrypt and store secret"""
        return self.field_encryption.encrypt(value)
    
    def retrieve_secret(self, encrypted_value: str) -> Optional[str]:
        """Retrieve and decrypt secret"""
        return self.field_encryption.decrypt(encrypted_value)
    
    def store_api_keys(self, keys: Dict[str, str]) -> Dict[str, str]:
        """Store multiple API keys securely"""
        return {k: self.store_secret(v) for k, v in keys.items()}
    
    def retrieve_api_keys(self, encrypted_keys: Dict[str, str]) -> Dict[str, str]:
        """Retrieve multiple API keys"""
        return {k: self.retrieve_secret(v) for k, v in encrypted_keys.items()}


# Convenience functions
def get_field_encryption() -> FieldEncryption:
    """Get field encryption instance"""
    return FieldEncryption()


def get_aes_encryption() -> AES256GCM:
    """Get AES-GCM encryption instance"""
    return AES256GCM()


def get_rsa_encryption() -> RSAEncryption:
    """Get RSA encryption instance"""
    return RSAEncryption.generate_key_pair()


def get_token_encryption() -> TokenEncryption:
    """Get token encryption instance"""
    return TokenEncryption()


def get_secure_storage() -> SecureStorage:
    """Get secure storage instance"""
    return SecureStorage()


# Sensitive fields that should always be encrypted
SENSITIVE_FIELDS = [
    'password_hash',
    'email',
    'phone',
    'bvn',
    'nin',
    'bank_account',
    'bank_code',
    'account_number',
    'card_number',
    'cvv',
    'expiry_date',
    'pin',
    'secret_question',
    'secret_answer',
    'api_key',
    'secret_key',
    'private_key',
    'access_token',
    'refresh_token',
    'api_secret',
    'webhook_secret',
]


def encrypt_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt all sensitive fields in a dictionary"""
    encryption = get_field_encryption()
    result = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in result and result[field] is not None:
            result[field] = encryption.encrypt(str(result[field]))
    return result


def decrypt_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields in a dictionary"""
    encryption = get_field_encryption()
    result = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in result and result[field] is not None:
            result[field] = encryption.decrypt(result[field])
    return result