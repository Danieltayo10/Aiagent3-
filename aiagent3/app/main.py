from fastapi import FastAPI
import sys

print("=== APP IMPORT STARTED ===")
print("Python version:", sys.version)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive"}

@app.get("/healthz")
def healthz():
    return {"ok": True}

print("=== APP READY ===")
