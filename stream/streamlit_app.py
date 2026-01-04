import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Autonomous AI Agent", layout="wide")

# ------------------------------
# Base API URL
# ------------------------------
API_BASE = "https://aiagentfastapi.onrender.com/api"

# ------------------------------
# Session State Initialization
# ------------------------------
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

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
            timeout=15
        )
    except Exception as e:
        st.exception(e)
        return

    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["logged_in_user"] = username
        st.success(f"Registered & logged in as {username}")
    else:
        st.error(res.text)

def login_user(username: str, password: str):
    try:
        res = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=15
        )
    except Exception as e:
        st.exception(e)
        return

    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["logged_in_user"] = username
        st.success(f"Logged in as {username}")
    else:
        st.error(res.text)

def get_auth_headers():
    token = st.session_state.get("jwt_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

# ------------------------------
# Protected Actions
# ------------------------------
def upload_document(file):
    st.info("🚀 Upload started")

    headers = get_auth_headers()
    if not headers:
        st.error("❌ Not authenticated")
        return

    st.write("📄 File:", file.name)
    st.write("📦 Type:", file.type)
    st.write("📏 Size:", file.size)

    try:
        with st.spinner("Uploading document..."):
            res = requests.post(
                f"{API_BASE}/ingest",
                files={
                    "file": (
                        file.name,
                        file.getvalue(),   # 🔥 IMPORTANT FIX
                        file.type
                    )
                },
                headers=headers,
                timeout=30
            )
    except requests.exceptions.Timeout:
        st.error("⏱️ Upload timed out (backend not responding)")
        return
    except Exception as e:
        st.error("🔥 Upload exception")
        st.exception(e)
        return

    st.write("🔁 Status:", res.status_code)
    st.write("🧾 Response:", res.text)

    if res.status_code == 200:
        st.success("✅ Document uploaded successfully")
    else:
        st.error("❌ Upload failed")

def ask_question(query: str, sms_number: str | None):
    headers = get_auth_headers()
    if not headers:
        st.error("Not authenticated")
        return

    payload = {"query": query}
    if sms_number:
        payload["send_sms_to"] = sms_number

    try:
        with st.spinner("Thinking..."):
            res = requests.post(
                f"{API_BASE}/query",
                json=payload,
                headers=headers,
                timeout=30
            )
    except Exception as e:
        st.exception(e)
        return

    if res.status_code == 200:
        st.subheader("AI Answer")
        st.write(res.json()["answer"])
    else:
        st.error(res.text)

# ------------------------------
# Sidebar: Authentication
# ------------------------------
st.sidebar.title("User Authentication")

if st.session_state.get("logged_in_user"):
    st.sidebar.success(f"Logged in as {st.session_state['logged_in_user']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
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

if not st.session_state.get("logged_in_user"):
    st.info("Please log in to upload documents or ask questions.")
else:
    st.subheader("Upload Documents")
    file = st.file_uploader("PDF, TXT, DOCX", type=["pdf", "txt", "docx"])

    if file:
        if st.button("Upload"):
            upload_document(file)

    st.subheader("Ask a Question")
    query = st.text_input("Your question")
    sms_number = st.text_input("Send summary via SMS (optional)")

    if st.button("Ask AI"):
        ask_question(query, sms_number if sms_number else None)
