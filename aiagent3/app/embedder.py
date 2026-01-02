import numpy as np

_model = None  # private global variable

def get_model():
    global _model
    if _model is None:
        # lazy-load only on first use
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_embedding(text: str):
    model = get_model()
    return np.array(model.encode(text), dtype="float32")
