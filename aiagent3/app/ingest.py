from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from docx import Document
import fitz  # PyMuPDF
import numpy as np
import pickle
import os
import time
import logging
import threading

from app.index import add_embeddings
from app.embedder import get_embedding

# --------------------------------
# Router & Logging
# --------------------------------
router = APIRouter()
logging.basicConfig(level=logging.INFO)

# --------------------------------
# JWT config
# --------------------------------
JWT_SECRET = "supersecretkey123"
ALGORITHM = "HS256"
security = HTTPBearer()

# --------------------------------
# Ephemeral storage (Render)
# --------------------------------
FAISS_DIR = os.path.join("/tmp", "faiss_index")
STATUS_DIR = os.path.join("/tmp", "ingest_status")
LOCK_DIR = os.path.join("/tmp", "ingest_lock")

os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)
os.makedirs(LOCK_DIR, exist_ok=True)

# --------------------------------
# Helper: decode JWT & get user ID
# --------------------------------
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --------------------------------
# Helper: read uploaded file
# --------------------------------
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
        raise HTTPException(status_code=400, detail="Unsupported file type")

# --------------------------------
# Status helpers
# --------------------------------
def status_path(user_id: int):
    return os.path.join(STATUS_DIR, f"{user_id}.txt")

def lock_path(user_id: int):
    return os.path.join(LOCK_DIR, f"{user_id}.lock")

def set_status(user_id: int, status: str):
    with open(status_path(user_id), "w") as f:
        f.write(status)

def get_status(user_id: int):
    path = status_path(user_id)
    if not os.path.exists(path):
        return "idle"
    return open(path).read().strip()

# --------------------------------
# Background processing pipeline
# --------------------------------
def process_file_background(user_id: int, text: str):
    lockfile = lock_path(user_id)

    # Prevent parallel ingestion
    if os.path.exists(lockfile):
        logging.warning(f"[INGEST] User {user_id} already ingesting")
        return

    # Acquire lock
    open(lockfile, "w").close()

    start_time = time.time()
    logging.info(f"[INGEST] Starting processing for user {user_id}")
    set_status(user_id, "processing")

    try:
        # Split into chunks
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        logging.info(f"[INGEST] Total chunks: {len(chunks)}")

        # Generate embeddings (DO NOT HOLD ALL IN MEMORY IF HUGE)
        embeddings_list = []
        for i, c in enumerate(chunks):
            emb = get_embedding(c)
            embeddings_list.append(emb)
            if i % 10 == 0:
                logging.info(f"[INGEST] Embedded {i}/{len(chunks)}")

        embeddings = np.stack(embeddings_list)
        logging.info(f"[INGEST] Embeddings generated")

        # Update FAISS index
        add_embeddings(user_id, embeddings)
        logging.info(f"[INGEST] FAISS index updated")

        # Save chunks
        chunks_path = os.path.join(FAISS_DIR, f"{user_id}_chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)
        logging.info(f"[INGEST] Chunks saved")

        set_status(user_id, "completed")
        logging.info(f"[INGEST] Finished in {time.time() - start_time:.2f}s")

    except Exception as e:
        logging.exception(f"[INGEST] FAILED for user {user_id}: {e}")
        set_status(user_id, "failed")

    finally:
        # Release lock
        try:
            os.remove(lockfile)
        except:
            pass

# --------------------------------
# POST /ingest  (NON-BLOCKING)
# --------------------------------
@router.post("/ingest")
def ingest(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id),
):
    # Mark as processing IMMEDIATELY (before thread)
    set_status(user_id, "processing")

    text = read_file(file)

    t = threading.Thread(
        target=process_file_background,
        args=(user_id, text),
        daemon=True
    )
    t.start()

    return {
        "status": "accepted",
        "message": "File is being processed in background"
    }

# --------------------------------
# GET /ingest/status/me
# --------------------------------
@router.get("/ingest/status/me")
def ingest_status_me(user_id: int = Depends(get_user_id)):
    return {"status": get_status(user_id)}
