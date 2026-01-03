# app/routes/ingest.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.index import add_embeddings, get_index, save_index
from app.embedder import get_embedding
from app.security import decode_access_token
import numpy as np
import fitz  # PyMuPDF for PDF
from docx import Document
import pickle, os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

router = APIRouter()
ALGORITHM = "HS256"
security = HTTPBearer()

# ------------------------------
# JWT secret from environment (fallback for local)
# ------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey123")

# ------------------------------
# FAISS index directory (use /tmp on Render)
# ------------------------------
FAISS_DIR = "/tmp/faiss_index"
os.makedirs(FAISS_DIR, exist_ok=True)

# ------------------------------
# JWT dependency
# ------------------------------
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------------------
# File reader
# ------------------------------
def read_file(file: UploadFile):
    ext = file.filename.split(".")[-1].lower()
    if ext == "txt":
        return file.file.read().decode("utf-8", errors="ignore")
    elif ext == "pdf":
        doc = fitz.open(stream=file.file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif ext == "docx":
        doc = Document(file.file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        raise HTTPException(400, "Unsupported file type")

# ------------------------------
# Endpoint: Ingest file
# ------------------------------
@router.post("/ingest")
async def ingest(file: UploadFile = File(...), user_id: int = Depends(get_user_id)):
    text = read_file(file)
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    embeddings = np.stack([get_embedding(c) for c in chunks])

    # Replace old embeddings for this user
    add_embeddings(user_id, embeddings)

    # Save chunks (overwrite old)
    chunks_path = os.path.join(FAISS_DIR, f"{user_id}_chunks.pkl")
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    return {"status": "success", "chunks": len(chunks)}
