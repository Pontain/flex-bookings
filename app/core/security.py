import hashlib
from fastapi import HTTPException
from pwdlib import PasswordHash
from email_validator import validate_email, EmailNotValidError
password_hash = PasswordHash.recommended()
def validate_password(password):
    if not 12 <= len(password) <= 128:
        raise HTTPException(400, "Lösenordet måste ha 12–128 tecken.")
    return password
def hash_password(password): return password_hash.hash(validate_password(password))
def verify_password(plain_password, hashed_password):
    if len(plain_password) > 128: return False
    try: return password_hash.verify(plain_password, hashed_password)
    except Exception: return False
def normalize_email(value):
    try: return validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError: raise HTTPException(400, "Ogiltig e-postadress.")
def digest(token): return hashlib.sha256(token.encode()).hexdigest()
