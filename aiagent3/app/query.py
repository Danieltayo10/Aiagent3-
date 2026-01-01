# app/routes/query.py
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv
import os
import requests
import numpy as np
import pickle
from typing import Optional
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security import decode_access_token
from app.index import get_index
from app.embedder import get_embedding
from app.clientell import client  # your OpenAI client

load_dotenv()

router = APIRouter()
security = HTTPBearer()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # SMS-enabled Twilio number

# -----------------------------
# JWT dependency
# -----------------------------
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    try:
        data = decode_access_token(token)
        return data["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# -----------------------------
# Request model
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    send_sms_to: Optional[str] = None

# -----------------------------
# Summarization helper
# -----------------------------
def summarize_text(text: str) -> str:
    sentences = text.split(".")
    summary = ".".join(sentences[:2]).strip()
    if not summary.endswith("."):
        summary += "."
    return summary

# -----------------------------
# Endpoint: Query + SMS
# -----------------------------
@router.post("/query")
async def query_agent(request: QueryRequest, user_id: int = Depends(get_user_id)):

    query = request.query
    index = get_index(user_id)
    
    if index.ntotal == 0:
        return {"answer": "No documents ingested yet."}

    qvec = np.expand_dims(get_embedding(query), axis=0)
    D, I = index.search(qvec, k=min(3, index.ntotal))

    chunks_path = f"app/faiss_index/{user_id}_chunks.pkl"
    if not os.path.exists(chunks_path):
        return {"answer": "No document chunks found for this user."}

    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    retrieved_texts = [chunks[i] for i in I[0] if i < len(chunks)]

    prompt = (
        "You are an assistant. Use the following context to answer the question:\n\n"
        f"Context:\n{chr(10).join(retrieved_texts)}\n\n"
        f"Question: {query}\nAnswer:"
    )

    try:
        response = client.chat(
            system="You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response["content"]
    except Exception as e:
        answer = "LLM failed to generate answer: " + str(e)

    # -----------------------------
    # Send via SMS if requested
    # -----------------------------
    if request.send_sms_to:
        try:
            summary = summarize_text(answer)
            payload = {
                "From": TWILIO_SMS_NUMBER,
                "To": request.send_sms_to,
                "Body": summary
            }
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            sms_response = requests.post(url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
            if not sms_response.ok:
                answer += f"\n\n(Warning: Failed to send SMS: {sms_response.text})"
        except Exception as e:
            answer += f"\n\n(Warning: SMS send failed: {e})"

    return {"answer": answer}

