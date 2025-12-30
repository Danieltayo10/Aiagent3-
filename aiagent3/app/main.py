# app/main.py
import sys
import traceback
from fastapi import FastAPI
import os

print("=== APP IMPORT STARTED ===")

app = FastAPI(title="Autonomous Multi-Client AI Agent")

# Include routers safely
try:
    from app import auth, ingest, query, automation
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(ingest.router, prefix="/api", tags=["ingest"])
    app.include_router(query.router, prefix="/api", tags=["query"])
    app.include_router(automation.router, prefix="/api", tags=["automation"])
    print("Routers imported successfully")
except Exception as e:
    print("=== ROUTER IMPORT ERROR ===")
    traceback.print_exc()

# Database initialization at startup
@app.on_event("startup")
async def startup_event():
    try:
        from app.database import Base, engine
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
    except Exception as e:
        print("=== DATABASE INIT ERROR ===")
        traceback.print_exc()
        # Don't crash app — optional: you could sys.exit(1) if you want
