import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Autonomous AI Agent", layout="wide")

# ------------------------------
# Base API URL
# ------------------------------
API_BASE = "https://aiagentfastapi.onrender.com"

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
    res = requests.post(
        f"{API_BASE}/auth/register",
        json={"username": username, "password": password}
    )
    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["logged_in_user"] = username
        st.success(f"Registered & logged in as {username}")
    else:
        st.error(res.json().get("detail", "Registration failed"))

def login_user(username: str, password: str):
    if len(password) > 72:
        st.error("Password too long (max 72 characters)")
        return
    res = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password}
    )
    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["logged_in_user"] = username
        st.success(f"Logged in as {username}")
    else:
        st.error(res.json().get("detail", "Login failed"))

def get_auth_headers():
    token = st.session_state.get("jwt_token")
    if not token:
        st.warning("You must login first")
        return None
    return {"Authorization": f"Bearer {token}"}

# ------------------------------
# Protected Actions
# ------------------------------
def upload_document(file):
    headers = get_auth_headers()
    if not headers:
        return

    res = requests.post(
        f"{API_BASE}/ingest",
        files={"file": (file.name, file, file.type)},
        headers=headers
    )

    if res.status_code == 200:
        st.success("Document uploaded")
    else:
        st.error(res.json().get("detail", "Upload failed"))

def ask_question(query: str, sms_number: str | None):
    headers = get_auth_headers()
    if not headers:
        return

    payload = {"query": query}

    if sms_number:
        payload["send_sms_to"] = sms_number  # ✅ matches query.py exactly

    res = requests.post(
        f"{API_BASE}/query",
        json=payload,
        headers=headers
    )

    if res.status_code == 200:
        answer = res.json()["answer"]
        st.subheader("AI Answer")
        st.write(answer)

        if sms_number:
            st.success(f"📩 Answer summary sent via SMS to {sms_number}")
    else:
        st.error(res.json().get("detail", "Query failed"))

# ------------------------------
# Sidebar: Authentication
# ------------------------------
st.sidebar.title("User Authentication")

if st.session_state.get("logged_in_user"):
    st.sidebar.success(f"Logged in as {st.session_state['logged_in_user']}")
    if st.sidebar.button("Logout"):
        st.session_state["jwt_token"] = None
        st.session_state["logged_in_user"] = None
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

# Upload docs
st.subheader("Upload Documents")
file = st.file_uploader("PDF, TXT, DOCX", type=["pdf", "txt", "docx"])
if file and st.button("Upload"):
    upload_document(file)

# Query + SMS
st.subheader("Ask a Question")
query = st.text_input("Your question")
sms_number = st.text_input(
    "Send summary via SMS (optional, e.g. +2349123456789)"
)

if st.button("Ask AI"):
    ask_question(query, sms_number if sms_number else None)
