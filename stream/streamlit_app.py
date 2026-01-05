import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Autonomous AI Agent", layout="wide")

# ------------------------------
# Base API URL
# ------------------------------
API_BASE = "https://aiagent3-1.onrender.com/api"

# ------------------------------
# Session State Initialization
# ------------------------------
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

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
            timeout=100
        )
    except Exception as e:
        st.error("🔥 Registration exception")
        st.exception(e)
        return

    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["user_id"] = username
        st.success(f"Registered & logged in as {username}")
    else:
        st.error(f"❌ Registration failed: {res.text}")


def login_user(username: str, password: str):
    try:
        res = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=70
        )
    except Exception as e:
        st.error("🔥 Login exception")
        st.exception(e)
        return

    if res.status_code == 200:
        st.session_state["jwt_token"] = res.json()["access_token"]
        st.session_state["user_id"] = username
        st.success(f"Logged in as {username}")
    else:
        st.error(f"❌ Login failed: {res.text}")


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
        # Send file to /ingest (background processing)
        with st.spinner("Uploading document..."):
            res = requests.post(
                f"{API_BASE}/ingest",
                files={
                    "file": (
                        file.name,
                        file.getvalue(),
                        file.type
                    )
                },
                headers=headers,
                timeout=100  # Keep small; backend returns immediately
            )

        if res.status_code != 200:
            st.error(f"❌ Upload failed with status {res.status_code}")
            try:
                error_json = res.json()
                st.error(f"Backend response: {error_json}")
                if "detail" in error_json:
                    st.error(f"Detail: {error_json['detail']}")
            except Exception:
                st.error(f"Backend response (raw): {res.text}")
            return

        st.success("✅ Document uploaded successfully! Processing in background.")

        # -------------------------
        # Polling backend for completion
        # -------------------------
        chunks_path_check = f"{API_BASE}/ingest/status/{st.session_state['user_id']}"  # must match user_id
        import time

        with st.spinner("Waiting for processing to complete..."):
            for i in range(30):  # poll up to 30 times (~30 sec)
                status_res = requests.get(chunks_path_check, headers=headers, timeout=5)
                if status_res.status_code == 200 and status_res.json().get("status") == "completed":
                    st.success("✅ Processing completed!")
                    break
                time.sleep(1)
            else:
                st.info("⏳ Processing still ongoing. You can continue using the app.")

    except requests.exceptions.RequestException as e:
        st.error("🔥 Upload exception (requests)")
        st.exception(e)
    except Exception as e:
        st.error("🔥 Upload exception (general)")
        st.exception(e)



def ask_question(query: str, sms_number: str | None):
    headers = get_auth_headers()
    if not headers:
        st.error("❌ Not authenticated")
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
                timeout=120  # increased timeout
            )

        if res.status_code != 200:
            st.error(f"❌ Query failed with status {res.status_code}")
            try:
                error_json = res.json()
                st.error(f"Backend response: {error_json}")
                if "detail" in error_json:
                    st.error(f"Detail: {error_json['detail']}")
            except Exception:
                st.error(f"Backend response (raw): {res.text}")
            return

        st.subheader("AI Answer")
        st.write(res.json()["answer"])

        if sms_number:
            st.success(f"📩 Answer summary sent via SMS to {sms_number}")

    except requests.exceptions.RequestException as e:
        st.error("🔥 Query exception (requests)")
        st.exception(e)
    except Exception as e:
        st.error("🔥 Query exception (general)")
        st.exception(e)


# ------------------------------
# Sidebar: Authentication
# ------------------------------
st.sidebar.title("User Authentication")

if st.session_state.get("user_id"):
    st.sidebar.success(f"Logged in as {st.session_state['user_id']}")
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

if not st.session_state.get("user_id"):
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





