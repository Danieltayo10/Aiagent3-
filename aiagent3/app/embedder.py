import os
import numpy as np
from openai import OpenAI

OPENROUTER_KEY = os.getenv("OpenAI_API_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

def get_embedding(text: str):
    # prevent giant inputs
    if len(text) > 8000:
        text = text[:8000]

    try:
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(res.data[0].embedding, dtype="float32")
    except Exception as e:
        print(f"Embedding API call failed: {e}")
        return np.zeros(1536, dtype="float32")  # fallback vector
