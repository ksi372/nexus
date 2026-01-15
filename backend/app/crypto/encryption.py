"""
Neural Cipher - AES Encryption using TPM-derived keys

Uses AES-256-GCM for authenticated encryption with keys
derived from synchronized Tree Parity Machines.
"""

import os
import base64
import hashlib
from typing import Tuple
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class NeuralCipher:
    """
    AES-256-GCM encryption using TPM-derived keys
    
    GCM mode provides both confidentiality and authenticity,
    preventing tampering with encrypted messages.
    """
    
    def __init__(self, key: bytes):
        """
        Initialize cipher with TPM-derived key
        
        Args:
            key: 32-byte key from synchronized TPM weights
        """
        if len(key) < 32:
            # Extend key if needed using HKDF-like expansion
            key = hashlib.sha256(key).digest()
        self.key = key[:32]
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt message using AES-256-GCM
        
        Args:
            plaintext: Message to encrypt
            
        Returns:
            Base64-encoded ciphertext with nonce and tag
        """
        # Generate random nonce (96 bits for GCM)
        nonce = get_random_bytes(12)
        
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        
        # Encrypt and get authentication tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # Combine: nonce + tag + ciphertext
        combined = nonce + tag + ciphertext
        
        return base64.b64encode(combined).decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt message using AES-256-GCM
        
        Args:
            encrypted: Base64-encoded ciphertext
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If decryption or authentication fails
        """
        try:
            combined = base64.b64decode(encrypted.encode('utf-8'))
            
            # Extract components
            nonce = combined[:12]
            tag = combined[12:28]
            ciphertext = combined[28:]
            
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
            
            # Decrypt and verify authentication tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def get_key_fingerprint(self) -> str:
        """Get short fingerprint of the key for verification"""
        return hashlib.sha256(self.key).hexdigest()[:8].upper()


def derive_key_from_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """
    Derive encryption key from password using PBKDF2
    
    Useful for local storage encryption.
    
    Args:
        password: User password
        salt: Salt bytes (generated if not provided)
        
    Returns:
        Tuple of (key, salt)
    """
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256
    
    if salt is None:
        salt = get_random_bytes(16)
    
    key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
    
    return key, salt
