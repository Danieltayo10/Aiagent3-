import streamlit as st
import requests
from dotenv import load_dotenv
import time

load_dotenv()

# ------------------------------
# Base API URL
# ------------------------------
API_BASE = "https://aiagentfast.onrender.com/api"

# ------------------------------
# Session State Initialization
# ------------------------------
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "upload_status" not in st.session_state:
    st.session_state["upload_status"] = None
if "last_poll" not in st.session_state:
    st.session_state["last_poll"] = 0

# ------------------------------
# Authentication Functions
# ------------------------------
def register_user(username: str, password: str):
    if len(password) > 72:
        st.error("Password too long (max 72 characters)")
        return
    try:
        res = requests.post(
            f"{API_BASE}/auth/register",
            json={"username": username, "password": password},
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        st.session_state["jwt_token"] = data["access_token"]
        st.session_state["logged_in_user"] = username
        st.session_state["user_id"] = data["user_id"]
        st.success(f"Registered & logged in as {username}")
    except Exception as e:
        st.error(f"Registration failed: {e}")

def login_user(username: str, password: str):
    if len(password) > 72:
        st.error("Password too long (max 72 characters)")
        return
    try:
        res = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        st.session_state["jwt_token"] = data["access_token"]
        st.session_state["logged_in_user"] = username
        st.session_state["user_id"] = data["user_id"]
        st.success(f"Logged in as {username}")
    except Exception as e:
        st.error(f"Login failed: {e}")

def get_auth_headers():
    token = st.session_state.get("jwt_token")
    if not token:
        st.warning("You must login first")
        return None
    return {"Authorization": f"Bearer {token}"}

# ------------------------------
# Document Upload
# ------------------------------
def upload_document(file):
    headers = get_auth_headers()
    if not headers:
        return

    try:
        res = requests.post(
            f"{API_BASE}/ingest",
            files={"file": (file.name, file, file.type)},
            headers=headers,
            timeout=15
        )
        res.raise_for_status()
        st.session_state["upload_status"] = "processing"
        st.session_state["last_poll"] = 0  # reset poll timer
        st.success("File uploaded! Processing has started.")
    except Exception as e:
        st.error(f"Upload failed: {e}")
        st.session_state["upload_status"] = None

# ------------------------------
# Poll Ingestion Status (Non-blocking)
# ------------------------------
def poll_status():
    if st.session_state["upload_status"] != "processing":
        return

    # Poll only every 5 minutes (300s)
    if time.time() - st.session_state["last_poll"] < 300:
        return
    st.session_state["last_poll"] = time.time()

    headers = get_auth_headers()
    if not headers:
        return

    try:
        res = requests.get(f"{API_BASE}/ingest/status/me", headers=headers, timeout=15)
        res.raise_for_status()
        status = res.json().get("status")
        status_box = st.empty()

        if status == "completed":
            status_box.success("✅ Processing completed!")
            st.session_state["upload_status"] = "done"
        elif status == "failed":
            status_box.error("❌ Processing failed. Please try again.")
            st.session_state["upload_status"] = None
        else:
            status_box.info("⏳ Processing... (Render may be cold starting)")
            st.rerun()  # rerun the script to continue polling
    except Exception as e:
        st.warning(f"Could not check status: {e}")
        # Keep status as processing; next poll in 5 mins

# ------------------------------
# Ask Question
# ------------------------------
def ask_question(query: str, sms_number: str | None = None):
    headers = get_auth_headers()
    if not headers:
        return

    payload = {"query": query}
    if sms_number:
        payload["send_sms_to"] = sms_number

    try:
        res = requests.post(
            f"{API_BASE}/query",
            json=payload,
            headers=headers,
            timeout=200
        )
        res.raise_for_status()
        answer = res.json()["answer"]
        st.subheader("AI Answer")
        st.write(answer)
        if sms_number:
            st.success(f"📩 Answer summary sent via SMS to {sms_number}")
    except Exception as e:
        st.error(f"Query failed: {e}")

# ------------------------------
# Sidebar: Authentication
# ------------------------------
st.sidebar.title("User Authentication")

if st.session_state.get("logged_in_user"):
    st.sidebar.success(f"Logged in as {st.session_state['logged_in_user']}")
    if st.sidebar.button("Logout"):
        st.session_state["jwt_token"] = None
        st.session_state["logged_in_user"] = None
        st.session_state["user_id"] = None
        st.session_state["upload_status"] = None
        st.session_state["last_poll"] = 0
        st.sidebar.info("Logged out")
else:
    mode = st.sidebar.selectbox("Mode", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button(mode):
        if mode == "Register":
            register_user(username, password)
        else:
            login_user(username, password)

# ------------------------------
# Main UI
# ------------------------------
st.title("Autonomous AI Agent (SMS Enabled)")

# Upload documents
st.subheader("Upload Documents")
file = st.file_uploader("PDF, TXT, DOCX", type=["pdf", "txt", "docx"])
if file and st.button("Upload"):
    upload_document(file)

# Poll ingestion status non-blocking
poll_status()

# Ask questions
st.subheader("Ask a Question")
query = st.text_input("Your question")
sms_number = st.text_input("Send summary via SMS (optional, e.g. +1(415) 555-0132)")
if st.button("Ask AI") and query.strip():
    ask_question(query, sms_number if sms_number else None)
