import numpy as np
import threading
import logging

_model = None
_model_lock = threading.Lock()

def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logging.info("[EMBEDDER] Loading SentenceTransformer model...")
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer("all-MiniLM-L12-v2")
                logging.info("[EMBEDDER] Model loaded successfully")
    return _model

def get_embedding(text: str):
    model = get_model()

    # Prevent insanely large inputs from killing RAM
    if len(text) > 4000:
        text = text[:4000]

    emb = model.encode(text, show_progress_bar=False)

    return np.array(emb, dtype="float32")

