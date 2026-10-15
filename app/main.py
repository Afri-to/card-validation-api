"""Card Validation API: entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Card Validation API",
    description="Validates test payment card numbers and records mock transactions.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Liveness check used by CI, Docker and the uptime monitor."""
    return {"status": "ok"}
