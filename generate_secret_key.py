#!/usr/bin/env python3
"""
Script to generate a secure secret key for JWT authentication.
Usage: python generate_secret_key.py
"""

import secrets
import string


def generate_secret_key(length: int = 64) -> str:
    """
    Generate a secure random secret key.
    
    Args:
        length: Length of the secret key (default: 64)
    
    Returns:
        A secure random string suitable for use as a secret key
    """
    # Use URL-safe base64 characters plus some special characters
    alphabet = string.ascii_letters + string.digits + "-_"
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return secret_key


if __name__ == "__main__":
    print("=" * 70)
    print("Secret Key Generator for Vamo Junto Backend")
    print("=" * 70)
    print()
    
    # Generate a 64-character secret key (recommended minimum is 32)
    secret_key = generate_secret_key(64)
    
    print("Generated Secret Key (64 characters):")
    print("-" * 70)
    print(secret_key)
    print("-" * 70)
    print()
    print("Add this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("IMPORTANT: Keep this key secret and never commit it to version control!")
    print("=" * 70)

