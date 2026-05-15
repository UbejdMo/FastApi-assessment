import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import authors, books, categories, loans, members, reports

# Read API key from environment variable.
# Defaults to "dev-secret-key" for local development if not set.
API_KEY = os.getenv("API_KEY", "dev-secret-key")

app = FastAPI(
    title="Library Lending System",
    description="Backend API for a small library that lends physical books to registered members.",
    version="0.1.0",
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    
    if request.method in {"POST", "PATCH", "DELETE"}:
        api_key = request.headers.get("x-api-key")
        if api_key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key"},
            )
    return await call_next(request)


app.include_router(categories.router)
app.include_router(authors.router)
app.include_router(members.router)
app.include_router(books.router)
app.include_router(loans.router)
app.include_router(reports.router)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "library": "open"}