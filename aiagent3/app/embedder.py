# app/embedder.py
import os
import requests
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

HF_TOKEN = os.getenv("HF_API_TOKEN")

if not HF_TOKEN:
    logging.warning("[EMBEDDER] HF_API_TOKEN is not set!")

API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def get_embedding(text: str):
    # prevent insanely large inputs
    if len(text) > 8000:
        text = text[:8000]

    logging.info("[EMBEDDER] Requesting embedding from HuggingFace...")

    try:
        r = requests.post(
            API_URL,
            headers=HEADERS,
            json={"inputs": text},
            timeout=60
        )
        r.raise_for_status()
    except Exception as e:
        logging.error(f"[EMBEDDER] HuggingFace request failed: {e}")
        raise

    data = r.json()

    # HF returns: [[384 floats]]
    if not isinstance(data, list) or not isinstance(data[0], list):
        raise RuntimeError(f"Unexpected HF response: {data}")

    vec = data[0]

    logging.info("[EMBEDDER] Embedding received successfully")

    return np.array(vec, dtype="float32")
