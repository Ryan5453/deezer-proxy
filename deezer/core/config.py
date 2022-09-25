import os
import secrets

auth_key = os.getenv("DEEZER_AUTH_KEY")
if not auth_key:
    print("DEEZER_AUTH_KEY is not set, generating a temporary random key. ")
    auth_key = secrets.token_urlsafe(32)
    print(f"Your temporary key is: {auth_key}")

master_key = os.getenv("DEEZER_MASTER_KEY")
if not master_key:
    print("DEEZER_MASTER_KEY is not set, please set it to the correct value.")
    print("Track decryption will not work and MP3 files will be invalid.")

redis_url = os.getenv("DEEZER_REDIS_URL", "redis://localhost:6379/0")
