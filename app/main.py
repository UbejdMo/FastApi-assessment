from fastapi import FastAPI

from app.routers import authors,books, categories, loans,members,reports

app = FastAPI(
    title="Library Lending System",
    description="Backend API for a small library that lends physical books to registered members.",
    version="0.1.0",
)

app.include_router(categories.router)
app.include_router(authors.router)
app.include_router(members.router)                   
app.include_router(books.router)                   
app.include_router(loans.router)                   
app.include_router(reports.router)                   


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "library": "open"}