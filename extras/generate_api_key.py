#!/usr/bin/env python3
"""
Simple script to generate a secure API key for the application
"""

import secrets
import string

def generate_api_key(length=32):
    """Generate a secure API key"""
    # Use URL-safe characters for better compatibility
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    api_key = generate_api_key()
    print("🔑 Generated API Key:")
    print(f"   {api_key}")
    print()
    print("📝 Add this to your environment files:")
    print()
    print("Backend (.env):")
    print(f"   API_KEY={api_key}")
    print()
    print("Frontend (.env):")
    print(f"   VITE_API_KEY={api_key}")
    print()
    print("⚠️  Keep this key secure and don't share it!")
