# app/routes/ingest.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks
from app.index import add_embeddings, get_index, save_index
from app.embedder import get_embedding
from app.security import decode_access_token
import numpy as np
import fitz  # PyMuPDF for PDF
from docx import Document
import pickle, os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import time
from typing import Union

router = APIRouter()
JWT_SECRET = "supersecretkey123"
ALGORITHM = "HS256"
security = HTTPBearer()

# Use /tmp for ephemeral storage on Render
FAISS_DIR = os.path.join("/tmp", "faiss_index")
os.makedirs(FAISS_DIR, exist_ok=True)

# -----------------------------
# JWT decode helper
# -----------------------------
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

# -----------------------------
# File reading
# -----------------------------
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

# -----------------------------
# Background processing
# -----------------------------
def process_file_background(user_id: int, text: str):
    start_time = time.time()
    print(f"[INFO] Starting processing for user {user_id}...")

    # Split into 500-char chunks (same as original logic)
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    print(f"[INFO] Total chunks to embed: {len(chunks)}")

    # Generate embeddings (synchronous, same logic)
    try:
        embeddings = np.stack([get_embedding(c) for c in chunks])
        print(f"[INFO] Embeddings generated successfully for user {user_id}")
    except Exception as e:
        print(f"[ERROR] Embedding generation failed for user {user_id}: {e}")
        return

    # Replace old embeddings for this user
    try:
        add_embeddings(user_id, embeddings)
        print(f"[INFO] FAISS index updated for user {user_id}")
    except Exception as e:
        print(f"[ERROR] FAISS update failed for user {user_id}: {e}")

    # Save chunks for retrieval
    chunks_path = os.path.join(FAISS_DIR, f"{user_id}_chunks.pkl")
    try:
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)
        print(f"[INFO] Chunks saved for user {user_id}")
    except Exception as e:
        print(f"[ERROR] Saving chunks failed for user {user_id}: {e}")

    print(f"[INFO] Finished processing for user {user_id} in {time.time() - start_time:.2f}s")

# -----------------------------
# POST /ingest
# -----------------------------
@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id),
    background_tasks: BackgroundTasks = None
):
    # Read file (synchronously, quick)
    text = read_file(file)

    # Schedule heavy work in background
    background_tasks.add_task(process_file_background, user_id, text)

    # Immediate response
    return {"status": "accepted", "message": "File is being processed in background"}

# -----------------------------
# GET /ingest/status/{user_id}
# -----------------------------
@router.get("/ingest/status/{user_id}")
def ingest_status(user_id: Union[int,str]):
    chunks_path = os.path.join(FAISS_DIR, f"{user_id}_chunks.pkl")
    if os.path.exists(chunks_path):
        return {"status": "completed"}
    return {"status": "processing"}


