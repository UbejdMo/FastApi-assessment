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

```bash
# Set the API key (required for write operations)
export API_KEY=your-secret-key     # Linux/macOS
$env:API_KEY="your-secret-key"     # Windows PowerShell

# Run the development server
uvicorn app.main:app --reload
```
## API key

All `POST`, `PATCH`, and `DELETE` endpoints require an `X-API-Key` header. `GET` endpoints are open.

Set the key via the `API_KEY` environment variable before starting the server:

```bash
# Linux / macOS
export API_KEY=your-secret-key
uvicorn app.main:app --reload

# Windows PowerShell
$env:API_KEY="your-secret-key"
uvicorn app.main:app --reload

# Windows CMD
set API_KEY=your-secret-key
uvicorn app.main:app --reload
```

If `API_KEY` is not set, the server defaults to `dev-secret-key` (development only — not safe for production).

To test a protected endpoint, include the header:
```
X-API-Key: your-secret-key
```
In the Swagger UI at `/docs`, use the **Authorize** button (top right) to set the key once for all requests.

# Run the test suite
pytest tests/ -v

## Endpoints

- `GET /api/v1/health` — health check, returns `{"status": "ok", "library": "open"}`
- `/api/v1/categories` — CRUD for book categories (list, retrieve, create, update, delete)
- `/api/v1/authors` — CRUD for authors
- `/api/v1/members` — CRUD for library members
- `/api/v1/books` — CRUD for books (response embeds category and authors)
- `/api/v1/loans` — borrow a book, return a book, list loans with filters
- `GET /api/v1/books/search` — filtered, sorted, paginated book search
- `GET /api/v1/reports/top-borrowers` — top N members by total loans
- `GET /api/v1/reports/overdue-loans` — all currently overdue loans
- `GET /api/v1/books/{id}/loan-history` — paginated loan history per book
See `/docs` for the full interactive OpenAPI specification.

The API will be available at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI) at `http://127.0.0.1:8000/docs`.