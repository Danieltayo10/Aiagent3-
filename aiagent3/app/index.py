# app/faiss_index/index_manager.py
import faiss
import numpy as np
import os
from app.embedder import get_embedding

# ------------------------------
# Use /tmp for persistence on Render
# ------------------------------
FAISS_DIR = "/tmp/faiss_index"
os.makedirs(FAISS_DIR, exist_ok=True)

def get_index(user_id: int):
    """
    Get FAISS index for a user. Create a new one if it doesn't exist.
    """
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    if os.path.exists(path):
        return faiss.read_index(path)
    
    # Create new index for 384-dimensional embeddings
    return faiss.IndexFlatL2(384)

def save_index(user_id: int, index):
    """
    Save FAISS index to disk.
    """
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    faiss.write_index(index, path)

def add_embeddings(user_id: int, embeddings: np.ndarray):
    """
    Add new embeddings to a user's index and save.
    """
    index = get_index(user_id)
    index.add(embeddings)
    save_index(user_id, index)
