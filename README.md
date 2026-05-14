## Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Seed the database with test data
python scripts/seed.py

# Run the development server
uvicorn app.main:app --reload
```

## Endpoints

- `GET /api/v1/health` — health check, returns `{"status": "ok", "library": "open"}`
- `/api/v1/categories` — CRUD for book categories (list, retrieve, create, update, delete)
- `/api/v1/authors` — CRUD for authors
See `/docs` for the full interactive OpenAPI specification.

The API will be available at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI) at `http://127.0.0.1:8000/docs`.