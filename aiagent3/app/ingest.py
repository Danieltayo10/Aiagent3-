from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
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

def read_file(file: UploadFile):
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

@router.post("/ingest")
async def ingest(file: UploadFile = File(...), user_id: int = Depends(get_user_id)):
    try:
        # Ensure FAISS folder exists
        os.makedirs("/tmp/faiss_index", exist_ok=True)

        text = read_file(file)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        
        # compute embeddings safely
        embeddings = []
        for c in chunks:
            try:
                embeddings.append(get_embedding(c))
            except Exception as e:
                print(f"Warning: embedding failed for chunk: {e}")
        embeddings = np.stack(embeddings)

        # Add embeddings to FAISS
        add_embeddings(user_id, embeddings)

        # Save chunks
        chunks_path = os.path.join("app/faiss_index", f"{user_id}_chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)

        return {"status": "success", "chunks": len(chunks)}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")

