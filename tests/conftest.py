"""Shared fixtures for the test suite.

Uses an in-memory SQLite database with StaticPool to ensure all
connections (fixture sessions + route handler sessions) see the
same database within a single test.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Author, Book, Category, Member

# In-memory SQLite — never touches library.db on disk.
# StaticPool ensures every SQLAlchemy connection uses the same
# underlying connection, so fixture-seeded data is visible to
# route handlers during the same test.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    """Create tables, yield a session, then drop tables for clean isolation."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """TestClient wired to the in-memory test database."""
    return TestClient(app)