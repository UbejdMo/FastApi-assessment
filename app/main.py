from fastapi import FastAPI

from app.routers import categories

app = FastAPI(
    title="Library Lending System",
    description="Backend API for a small library that lends physical books to registered members.",
    version="0.1.0"
)

app.include_router(categories.router)

@app.get("/api/v1/health")
def health():
    return {"status":"ok", "library":"open"}
