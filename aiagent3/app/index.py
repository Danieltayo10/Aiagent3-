# app/faiss_index/index_manager.py
import faiss
import numpy as np
import os
import logging

# Use /tmp for persistence on Render
FAISS_DIR = "/tmp/faiss_index"
os.makedirs(FAISS_DIR, exist_ok=True)

DEFAULT_DIM = 384  # must match your embedding output

def get_index(user_id: int):
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    if os.path.exists(path):
        try:
            return faiss.read_index(path)
        except Exception as e:
            logging.error(f"[FAISS] Failed to read index for user {user_id}: {e}")
    
    # New index
    logging.info(f"[FAISS] Creating new index for user {user_id}")
    return faiss.IndexFlatL2(DEFAULT_DIM)

def save_index(user_id: int, index):
    path = os.path.join(FAISS_DIR, f"{user_id}.index")
    try:
        faiss.write_index(index, path)
        logging.info(f"[FAISS] Index saved for user {user_id}")
    except Exception as e:
        logging.error(f"[FAISS] Failed to save index for user {user_id}: {e}")

def add_embeddings(user_id: int, embeddings: np.ndarray):
    try:
        index = get_index(user_id)

        # check dimension
        if index.d != embeddings.shape[1]:
            logging.warning(f"[FAISS] Dimension mismatch: index {index.d} vs embeddings {embeddings.shape[1]}. Recreating index.")
            index = faiss.IndexFlatL2(embeddings.shape[1])

        index.add(embeddings.astype(np.float32))
        save_index(user_id, index)
        logging.info(f"[FAISS] {len(embeddings)} embeddings added for user {user_id}")
    except Exception as e:
        logging.error(f"[FAISS] Failed to add embeddings for user {user_id}: {e}")
