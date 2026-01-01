import traceback
from fastapi import FastAPI

print("=== STEP 0: main.py imported ===", flush=True)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive"}

def trace(msg):
    print(f"🔍 {msg}", flush=True)

# --------------------
# Router imports (ONE BY ONE)
# --------------------
try:
    trace("importing auth")
    from app import auth
    trace("including auth")
    app.include_router(auth.router)

    trace("importing ingest")
    from app import ingest
    trace("including ingest")
    app.include_router(ingest.router)

    trace("importing query")
    from app import query
    trace("including query")
    app.include_router(query.router)

    trace("importing automation")
    from app import automation
    trace("including automation")
    app.include_router(automation.router)

    trace("ALL ROUTERS LOADED")
except Exception:
    trace("❌ ROUTER LOAD FAILED")
    traceback.print_exc()

# --------------------
# Startup (NON-BLOCKING)
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
