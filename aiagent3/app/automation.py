# app/automation.py
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv
import os
import requests
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_access_token

load_dotenv()

router = APIRouter()
security = HTTPBearer()

# ------------------------------
# Twilio credentials
# ------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Twilio SMS-enabled number

# ------------------------------
# JWT dependency
# ------------------------------
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        data = decode_access_token(token)
        return data["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------------------
# Helper: summarize text for SMS
# ------------------------------
def summarize_text(text: str) -> str:
    sentences = text.split(".")
    summary = ".".join(sentences[:2]).strip()
    if not summary.endswith("."):
        summary += "."
    return summary

# ------------------------------
# Endpoint: send SMS
# ------------------------------
@router.post("/send_sms")
def send_sms(msg: str, to_number: str, user_id: int = Depends(get_user_id)):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_SMS_NUMBER:
        raise HTTPException(status_code=500, detail="Twilio credentials not set")

    # Summarize the message
    summary = summarize_text(msg)

    # Prepare payload using Twilio requests pattern
    payload = {
        "From": TWILIO_SMS_NUMBER,
        "To": to_number,
        "Body": summary
    }

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    try:
        response = requests.post(url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS send failed: {e}")

    return {
        "status": "sent",
        "summary": summary,
        "twilio_response": response.json()
    }
