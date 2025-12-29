# app/faiss_index/index_manager.py
import faiss
import numpy as np
import os
from .embedder import get_embedding

FAISS_DIR = "app/faiss_index"
os.makedirs(FAISS_DIR, exist_ok=True)

def get_index(user_id: int):
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    if os.path.exists(path):
        return faiss.read_index(path)
    return faiss.IndexFlatL2(384)

def save_index(user_id: int, index):
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    faiss.write_index(index, path)

def add_embeddings(user_id: int, embeddings: np.ndarray):
    index = get_index(user_id)
    index.add(embeddings)
    save_index(user_id, index)