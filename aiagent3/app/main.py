import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("=== STEP 0: main.py imported ===", flush=True)

app = FastAPI(
    title="Autonomous Multi-Client AI Agent",
    version="1.0.0"
)

# --------------------
# CORS
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Root
# --------------------
@app.get("/")
def root():
    return {"status": "alive"}

def trace(msg: str):
    print(f"🔍 {msg}", flush=True)

# --------------------
# Routers (NO .router ANYWHERE)
# --------------------
try:
    trace("importing auth router")
    from app.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

    trace("importing ingest router")
    from app.ingest import router as ingest_router
    app.include_router(ingest_router, prefix="/api", tags=["ingest"])

    trace("importing query router")
    from app.query import router as query_router
    app.include_router(query_router, prefix="/api", tags=["query"])

    trace("importing automation router")
    from app.automation import router as automation_router
    app.include_router(automation_router, prefix="/api", tags=["automation"])

    trace("ALL ROUTERS LOADED SUCCESSFULLY")

except Exception:
    trace("❌ ROUTER LOAD FAILED")
    traceback.print_exc()
    raise  # 🚨 FAIL FAST so you SEE the error

# --------------------
# Startup (DB init)
# --------------------
@app.on_event("startup")
async def startup():
    trace("startup entered")
    try:
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        trace("db ready")
    except Exception:
        trace("⚠️ db init failed")
        traceback.print_exc()
        raise
