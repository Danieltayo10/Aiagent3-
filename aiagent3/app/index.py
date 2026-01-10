# app/faiss_index/index_manager.py
import faiss
import numpy as np
import os
import logging
import time

# Use /tmp for persistence on Render
FAISS_DIR = "/tmp/faiss_index"
LOCK_DIR = "/tmp/faiss_locks"

os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs(LOCK_DIR, exist_ok=True)

DEFAULT_DIM = 384  # must match your embedding output

def _index_path(user_id: int):
    return os.path.join(FAISS_DIR, f"{user_id}.index")

def _lock_path(user_id: int):
    return os.path.join(LOCK_DIR, f"{user_id}.lock")

def _acquire_lock(user_id: int, timeout=60):
    lock = _lock_path(user_id)
    start = time.time()
    while os.path.exists(lock):
        if time.time() - start > timeout:
            raise RuntimeError("Timeout waiting for FAISS lock")
        time.sleep(0.2)
    open(lock, "w").close()

def _release_lock(user_id: int):
    try:
        os.remove(_lock_path(user_id))
    except:
        pass

def get_index(user_id: int):
    path = _index_path(user_id)
    if os.path.exists(path):
        try:
            return faiss.read_index(path)
        except Exception as e:
            logging.error(f"[FAISS] Failed to read index for user {user_id}: {e}")
    
    # New index
    logging.info(f"[FAISS] Creating new index for user {user_id}")
    return faiss.IndexFlatL2(DEFAULT_DIM)

def save_index(user_id: int, index):
    path = _index_path(user_id)
    tmp_path = path + ".tmp"

    try:
        faiss.write_index(index, tmp_path)
        os.replace(tmp_path, path)  # atomic replace
        logging.info(f"[FAISS] Index saved for user {user_id}")
    except Exception as e:
        logging.error(f"[FAISS] Failed to save index for user {user_id}: {e}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass

def add_embeddings(user_id: int, embeddings: np.ndarray):
    _acquire_lock(user_id)
    try:
        index = get_index(user_id)

        # check dimension
        if index.d != embeddings.shape[1]:
            logging.warning(
                f"[FAISS] Dimension mismatch: index {index.d} vs embeddings {embeddings.shape[1]}. Recreating index."
            )
            index = faiss.IndexFlatL2(embeddings.shape[1])

        index.add(embeddings.astype(np.float32))
        save_index(user_id, index)

        logging.info(f"[FAISS] {len(embeddings)} embeddings added for user {user_id}")
    except Exception as e:
        logging.error(f"[FAISS] Failed to add embeddings for user {user_id}: {e}")
        raise
    finally:
        _release_lock(user_id)
