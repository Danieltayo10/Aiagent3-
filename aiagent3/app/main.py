
from app import auth, ingest, query, automation
from app.database import Base, engine

import sys
import traceback

print("=== APP IMPORT STARTED ===")

try:
    # Everything below this line
    from fastapi import FastAPI
    import os
    # Your other imports, DB connections, agent, etc.
    print("Imports successful")

except Exception as e:
    print("=== IMPORT ERROR ===")
    traceback.print_exc()
    sys.exit(1)  # Ensure Render sees the crash


# Create all tables
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Autonomous Multi-Client AI Agent")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(automation.router, prefix="/api", tags=["automation"])


