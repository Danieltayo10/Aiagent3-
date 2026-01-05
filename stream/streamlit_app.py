import streamlit as st
import requests
import time

# ---------------------------------
# CONFIG
# ---------------------------------
API_BASE = "https://aiagent3-1.onrender.com/api"  # CHANGE THIS

st.set_page_config(
    page_title="Autonomous AI Agent",
    layout="wide"
)

# ---------------------------------
# SESSION STATE
# ---------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------------------------------
# HELPERS
# ---------------------------------
def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_post(url, **kwargs):
    return requests.post(url, timeout=60, **kwargs)

def api_get(url, **kwargs):
    return requests.get(url, timeout=60, **kwargs)

# ---------------------------------
# SIDEBAR – AUTH
# ---------------------------------
st.sidebar.title("🔐 Authentication")

if not st.session_state.token:
    mode = st.sidebar.radio("Mode", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button(mode):
        endpoint = "/auth/login" if mode == "Login" else "/auth/register"
        try:
            r = api_post(
                f"{API_BASE}{endpoint}",
                json={"username": username, "password": password}
            )
            if r.ok:
                data = r.json()
                st.session_state.token = data["access_token"]
                st.session_state.user_id = data["user_id"]
                st.sidebar.success("Authenticated")
                st.rerun()
            else:
                st.sidebar.error(r.text)
        except Exception as e:
            st.sidebar.error(str(e))
else:
    st.sidebar.success(f"Logged in as user {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user_id = None
        st.rerun()

# ---------------------------------
# MAIN UI
# ---------------------------------
st.title("🤖 Autonomous Multi-Client AI Agent")

if not st.session_state.token:
    st.warning("Please login to continue.")
    st.stop()

tabs = st.tabs(["📄 Ingest", "🔎 Query", "📲 SMS Automation"])

# =================================
# INGEST TAB
# =================================
with tabs[0]:
    st.header("📄 Document Ingestion")

    uploaded = st.file_uploader(
        "Upload a document",
        type=["txt", "pdf", "docx"]
    )

    if uploaded and st.button("Ingest Document"):
        try:
           files = {"file": (uploaded.name, uploaded, uploaded.type)}
           r = api_post(f"{API_BASE}/ingest", headers=auth_headers(), files=files)
           st.success("File accepted for processing")
        except Exception as e:
            st.error(str(e))

    if st.button("Check Ingest Status"):
        try:
            r = api_get(
                f"{API_BASE}/ingest/status/{st.session_state.user_id}"
            )
            st.info(r.json()["status"])
        except Exception as e:
            st.error(str(e))

# =================================
# QUERY TAB
# =================================
with tabs[1]:
    st.header("🔎 Query Your Documents")

    query = st.text_area("Ask a question")
    sms_to = st.text_input("Optional: Send answer via SMS (E.164)")

    if st.button("Run Query"):
        payload = {"query": query}
        if sms_to:
            payload["send_sms_to"] = sms_to

        try:
            r = api_post(
                f"{API_BASE}/query",
                headers=auth_headers(),
                json=payload
            )
            if r.ok:
                st.success("Answer")
                st.write(r.json()["answer"])
            else:
                st.error(r.text)
        except Exception as e:
            st.error(str(e))

# =================================
# AUTOMATION / SMS TAB
# =================================
with tabs[2]:
    st.header("📲 Send SMS (Automation)")

    msg = st.text_area("Message")
    to_number = st.text_input("Recipient Number (E.164)")

    if st.button("Send SMS"):
        try:
            r = api_post(
                f"{API_BASE}/send_sms",
                headers=auth_headers(),
                params={
                    "msg": msg,
                    "to_number": to_number
                }
            )
            if r.ok:
                st.success("SMS Sent")
                st.json(r.json())
            else:
                st.error(r.text)
        except Exception as e:
            st.error(str(e))


