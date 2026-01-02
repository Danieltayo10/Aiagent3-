import traceback
from fastapi import FastAPI

print("=== STEP 0: main.py imported ===", flush=True)

app = FastAPI(
    title="Autonomous Multi-Client AI Agent",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "alive"}

def trace(msg: str):
    print(f"🔍 {msg}", flush=True)

# --------------------
# Routers
# --------------------
try:
    trace("importing auth")
    from app.auth import router as auth_router
    trace("including auth")
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])

    trace("importing ingest")
    from app.ingest import router as ingest_router
    trace("including ingest")
    app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])

    trace("importing query")
    from app.query import router as query_router
    trace("including query")
    app.include_router(query_router, prefix="/query", tags=["Query"])

    trace("importing automation")
    from app.automation import router as automation_router
    trace("including automation")
    app.include_router(automation_router, prefix="/automation", tags=["Automation"])

    trace("ALL ROUTERS LOADED SUCCESSFULLY")

except Exception:
    trace("❌ ROUTER LOAD FAILED")
    traceback.print_exc()

# --------------------
# Startup (DB init)
# --------------------
@app.on_event("startup")
async def startup():
    trace("startup entered")
    try:
        from app.database import Base, engine
        trace("creating tables")
        Base.metadata.create_all(bind=engine)
        trace("db ready")
    except Exception:
        trace("⚠️ db init failed")
        traceback.print_exc()
