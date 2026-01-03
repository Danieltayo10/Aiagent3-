from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks
from app.index import add_embeddings, get_index, save_index
from app.embedder import get_embedding
from app.security import decode_access_token
import numpy as np
import fitz  # PyMuPDF
from docx import Document
import pickle, os, traceback
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

router = APIRouter()
JWT_SECRET = "supersecretkey123"
ALGORITHM = "HS256"
security = HTTPBearer()

# -----------------------------
# Helper: decode JWT and get user
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
# Helper: read uploaded file
# -----------------------------
def read_file(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1].lower()
    try:
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"File read failed: {e}")

# -----------------------------
# Helper: process file in background
# -----------------------------
def process_file(file_data: UploadFile, user_id: int):
    try:
        # Use /tmp/faiss_index for Render writable storage
        faiss_dir = "/tmp/faiss_index"
        os.makedirs(faiss_dir, exist_ok=True)

        text = read_file(file_data)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]

        embeddings = []
        for c in chunks:
            try:
                embeddings.append(get_embedding(c))
            except Exception as e:
                print(f"Warning: embedding failed for chunk: {e}")
        if not embeddings:
            raise Exception("No embeddings generated.")

        embeddings = np.stack(embeddings)

        # Add to FAISS
        add_embeddings(user_id, embeddings)

        # Save chunks
        chunks_path = os.path.join(faiss_dir, f"{user_id}_chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)

        print(f"✅ Ingest complete for user {user_id}, {len(chunks)} chunks")

    except Exception:
        traceback.print_exc()
        print(f"❌ Ingest failed for user {user_id}")

# -----------------------------
# Endpoint: ingest document
# -----------------------------
@router.post("/ingest")
async def ingest(file: UploadFile = File(...), user_id: int = Depends(get_user_id), background_tasks: BackgroundTasks = None):
    """
    Uploads a document, splits it into chunks, computes embeddings, and stores them.
    Runs in background to avoid hanging the API on Render.
    """
    if background_tasks is None:
        raise HTTPException(status_code=500, detail="BackgroundTasks not available")

    # Add task to background
    background_tasks.add_task(process_file, file, user_id)

    return {"status": "processing", "message": "Document is being processed in the background"}
