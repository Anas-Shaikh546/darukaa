from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import conversation, evidence, recommendation
from app.services.retrieval.ingest import get_collection

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


@app.on_event("startup")
def _warm_up_retrieval_resources() -> None:
    """Load the Chroma collection + embedding model once at boot.

    Without this, get_collection() runs for the first time inside a
    request handler, and the SentenceTransformer load can exceed the
    request timeout in production.
    """
    get_collection()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}