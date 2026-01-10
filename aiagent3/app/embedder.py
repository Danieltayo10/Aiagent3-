import os
import requests
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

HF_TOKEN = os.getenv("HF_API_TOKEN")

if not HF_TOKEN:
    logging.warning("[EMBEDDER] HF_API_TOKEN is not set!")

API_URL = "https://router.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def get_embedding(text: str):
    # limit input size
    if len(text) > 8000:
        text = text[:8000]

    logging.info("[EMBEDDER] Requesting embedding from HuggingFace Router...")

    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)
        r.raise_for_status()
    except Exception as e:
        logging.error(f"[EMBEDDER] HuggingFace Router request failed: {e} | Response: {getattr(r,'text',None)}")
        raise

    data = r.json()

    # Expect [[float, float, ...]]
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected HF Router response: {data}")

    vec = data[0]

    logging.info("[EMBEDDER] Embedding received successfully")

    return np.array(vec, dtype="float32")
