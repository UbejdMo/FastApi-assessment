# Library Lending System API

A FastAPI backend for a small library that lends physical books to registered members. Built with FastAPI, SQLAlchemy, and SQLite.

## Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /api/v1/health` — health check, returns `{"status": "ok", "library": "open"}`

## Database schema

![Database schema](docs/schema.jpg)

Live editable version: [drawSQL](https://drawsql.app/teams/ubejd-morina/diagrams/fastapi)

## Notes

lighthouse