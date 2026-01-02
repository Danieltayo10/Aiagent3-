from jose import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os

# ------------------------------
# Password & JWT settings
# ------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_BCRYPT_BYTES = 72  # bcrypt limit in bytes

# ------------------------------
# Password hashing
# ------------------------------
def hash_password(password: str) -> str:
    # Encode to bytes and truncate to 72 bytes for bcrypt
    safe_password = password.encode("utf-8")[:MAX_BCRYPT_BYTES]
    return pwd_context.hash(safe_password)

def verify_password(plain: str, hashed: str) -> bool:
    # Encode to bytes and truncate to 72 bytes for bcrypt
    safe_plain = plain.encode("utf-8")[:MAX_BCRYPT_BYTES]
    return pwd_context.verify(safe_plain, hashed)

# ------------------------------
# JWT handling
# ------------------------------
def create_access_token(data: dict, expires_delta=None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
