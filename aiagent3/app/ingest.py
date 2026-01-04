# app/routes/ingest.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.index import add_embeddings
from app.embedder import get_embedding
import numpy as np
import fitz
from docx import Document
import pickle, os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from starlette.concurrency import run_in_threadpool

router = APIRouter()
ALGORITHM = "HS256"
security = HTTPBearer()

JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey123")

FAISS_DIR = "/tmp/faiss_index"
os.makedirs(FAISS_DIR, exist_ok=True)

# ------------------------------
# JWT dependency (unchanged)
# ------------------------------
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID missing")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------------------
# File reader (SYNC, but safe)
# ------------------------------
def read_file_bytes(contents: bytes, filename: str) -> str:
    ext = filename.split(".")[-1].lower()

    if ext == "txt":
        return contents.decode("utf-8", errors="ignore")

    elif ext == "pdf":
        doc = fitz.open(stream=contents, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)

    elif ext == "docx":
        from io import BytesIO
        doc = Document(BytesIO(contents))
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise HTTPException(400, "Unsupported file type")

# ------------------------------
# Endpoint: Ingest file (FIXED)
# ------------------------------
@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id)
):
    try:
        print("📥 File received:", file.filename)

        # ✅ async-safe read
        contents = await file.read()
        print("📏 Size:", len(contents))

        # ✅ offload parsing
        text = await run_in_threadpool(
            read_file_bytes, contents, file.filename
        )

        # ✅ chunking (cheap)
        chunks = [text[i:i + 500] for i in range(0, len(text), 500)]

        # ✅ offload embeddings (VERY IMPORTANT)
        embeddings = await run_in_threadpool(
            lambda: np.stack([get_embedding(c) for c in chunks])
        )

        # ✅ offload FAISS update
        await run_in_threadpool(add_embeddings, user_id, embeddings)

        # ✅ offload disk write
        chunks_path = os.path.join(FAISS_DIR, f"{user_id}_chunks.pkl")
        await run_in_threadpool(
            lambda: pickle.dump(chunks, open(chunks_path, "wb"))
        )

        print("✅ Ingest complete")

        return {"status": "success", "chunks": len(chunks)}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
