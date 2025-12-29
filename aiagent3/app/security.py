from jose import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os

# ------------------------------
# Password & JWT settings
# ------------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_BCRYPT_LENGTH = 172  # bcrypt limit

# ------------------------------
# Password hashing
# ------------------------------
def hash_password(password: str) -> str:
    # Truncate to 72 characters to avoid bcrypt error
    safe_password = password[:MAX_BCRYPT_LENGTH]
    return pwd_context.hash(safe_password)

def verify_password(plain: str, hashed: str) -> bool:
    # Truncate to 72 characters to match hash
    safe_plain = plain[:MAX_BCRYPT_LENGTH]
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
