# app/main.py
import sys
import traceback
from fastapi import FastAPI

print("=== APP STARTING ===")

app = FastAPI(title="Autonomous Multi-Client AI Agent")

# --------------------
# Routers
# --------------------
try:
    from app import auth, ingest, query, automation

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(ingest.router, prefix="/api", tags=["ingest"])
    app.include_router(query.router, prefix="/api", tags=["query"])
    app.include_router(automation.router, prefix="/api", tags=["automation"])

    print("✅ Routers loaded")
except Exception:
    print("❌ ROUTER IMPORT ERROR")
    traceback.print_exc()
    sys.exit(1)

# --------------------
# Startup event
# --------------------
@app.on_event("startup")
async def startup_event():
    try:
        from app.database import Base, engine
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database ready")
    except Exception:
        print("❌ DATABASE INIT ERROR")
        traceback.print_exc()



