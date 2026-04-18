from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# This is the master API backend for THRESHOLD
# 20 Subagents will populate the routers and services

app = FastAPI(
    title="THRESHOLD API",
    description="Climate Crisis Intelligence & Triage System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "THRESHOLD Code Blue Protocol Online"}
