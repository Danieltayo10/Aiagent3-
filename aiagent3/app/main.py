from fastapi import FastAPI
from . import auth, ingest, query, automation
from .database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Autonomous Multi-Client AI Agent")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(automation.router, prefix="/api", tags=["automation"])


