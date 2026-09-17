from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import conversation, evidence, recommendation

app = FastAPI(
    title="Darukaa",
    description="Biodiversity intelligence — Day 1: real-evidence retrieval pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://darukaa-rho.vercel.app",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(evidence.router)
app.include_router(recommendation.router)
app.include_router(conversation.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}