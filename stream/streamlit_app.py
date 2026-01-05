import streamlit as st
import requests
from dotenv import load_dotenv
import time

load_dotenv()

st.set_page_config(page_title="Autonomous AI Agent", layout="wide")

# =====================================================
# CONFIG
# =====================================================
API_BASE = "https://aiagent3-1.onrender.com/api"

# =====================================================
# SESSION STATE
# =====================================================
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# =====================================================
# HELPERS
# =====================================================
def auth_headers():
    if not st.session_state.jwt_token:
        return None
    return {
        "Authorization": f"Bearer {st.session_state.jwt_token}"
    }

# =====================================================
# AUTH
# =====================================================
def register_user(username, password):
    try:
        res = requests.post(
            f"{API_BASE}/auth/register",
            json={"username": username, "password": password},
            timeout=30
        )
    except Exception as e:
        st.error("Registration request failed")
        st.exception(e)
        return

    if res.status_code == 200:
        data = res.json()
        st.session_state.jwt_token = data["access_token"]
        st.session_state.user_id = data["user_id"]
        st.success("Registered and logged in")
    else:
        st.error(res.text)


def login_user(username, password):
    try:
        res = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=30
        )
    except Exception as e:
        st.error("Login request failed")
        st.exception(e)
        return

    if res.status_code == 200:
        data = res.json()
        st.session_state.jwt_token = data["access_token"]
        st.session_state.user_id = data["user_id"]
        st.success("Logged in successfully")
    else:
        st.error(res.text)

# =====================================================
# INGEST
# =====================================================
def upload_document(file):
    headers = auth_headers()
    if not headers:
        st.error("Not authenticated")
        return

    with st.spinner("Uploading file..."):
        try:
            res = requests.post(
                f"{API_BASE}/ingest",
                headers=headers,
                files={
                    "file": (file.name, file.getvalue(), file.type)
                },
                timeout=60
            )
        except Exception as e:
            st.error("Upload failed")
            st.exception(e)
            return

    if res.status_code != 200:
        st.error(res.text)
        return

    st.success("Upload accepted. Processing in background.")

    # -----------------------------
    # POLLING STATUS
    # -----------------------------
    status_url = f"{API_BASE}/ingest/status/{st.session_state.user_id}"

    with st.spinner("Processing document..."):
        for _ in range(30):
            try:
                status_res = requests.get(status_url, headers=headers, timeout=10)
                if status_res.status_code == 200:
                    status = status_res.json().get("status")
                    if status == "completed":
                        st.success("Document processing completed")
                        return
            except Exception:
                pass

            time.sleep(1)

    st.info("Still processing. You can continue using the app.")

# =====================================================
# QUERY
# =====================================================
def ask_question(query, sms_number=None):
    headers = auth_headers()
    if not headers:
        st.error("Not authenticated")
        return

    payload = {"query": query}
    if sms_number:
        payload["send_sms_to"] = sms_number

    with st.spinner("Thinking..."):
        try:
            res = requests.post(
                f"{API_BASE}/query",
                headers=headers,
                json=payload,
                timeout=120
            )
        except Exception as e:
            st.error("Query failed")
            st.exception(e)
            return

    if res.status_code != 200:
        st.error(res.text)
        return

    answer = res.json().get("answer", "")
    st.subheader("Answer")
    st.write(answer)

    if sms_number:
        st.success("SMS summary sent")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Authentication")

if st.session_state.user_id:
    st.sidebar.success(f"User ID: {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.jwt_token = None
        st.session_state.user_id = None
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

# =====================================================
# MAIN UI
# =====================================================
st.title("Autonomous AI Agent (FAISS + SMS)")

if not st.session_state.user_id:
    st.info("Please log in to continue")
    st.stop()

st.subheader("Upload Document")
file = st.file_uploader("Upload PDF, TXT, DOCX", type=["pdf", "txt", "docx"])

if file and st.button("Upload"):
    upload_document(file)

st.subheader("Ask a Question")
query = st.text_input("Your question")
sms_number = st.text_input("Send summary via SMS (optional)")

if st.button("Ask AI") and query:
    ask_question(query, sms_number if sms_number else None)
