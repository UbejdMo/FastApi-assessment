"""Tests for loan operations: borrow, return, and edge cases."""

from datetime import date, timedelta
import pytest
from app.models import Loan

HEADERS = {"X-API-Key": "dev-secret-key"}
DUE_DATE = str(date.today() + timedelta(days=14))


@pytest.fixture
def loan_data(db):
    """Seed the minimal data needed for loan tests."""
    from app.models import Category, Author, Book, Member

    cat = Category(name="Fiction")
    db.add(cat)
    db.commit()

    author = Author(full_name="Test Author", country="Albania")
    db.add(author)
    db.commit()

    # Book with exactly 2 copies — lets us test the 409 by filling both slots
    book = Book(
        title="Test Book",
        isbn="978-0-000-00001-0",
        category_id=cat.id,
        total_copies=2,
        published_year=2020,
    )
    book.authors = [author]
    db.add(book)
    db.commit()

    active = Member(
        full_name="Active Member",
        email="active@test.com",
        join_date=date.today(),
        is_active=True,
    )
    inactive = Member(
        full_name="Inactive Member",
        email="inactive@test.com",
        join_date=date.today(),
        is_active=False,
    )
    db.add_all([active, inactive])
    db.commit()

    return {"book": book, "active": active, "inactive": inactive}


# ── Borrow flow ───────────────────────────────────────────────

def test_borrow_valid_returns_201(client, loan_data):
    data = loan_data
    resp = client.post(
        "/api/v1/loans",
        json={"member_id": data["active"].id, "book_id": data["book"].id, "due_date": DUE_DATE},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["member_id"] == data["active"].id
    assert body["book_id"] == data["book"].id
    assert body["return_date"] is None         # active loan — not yet returned


def test_borrow_inactive_member_returns_400(client, loan_data):
    data = loan_data
    resp = client.post(
        "/api/v1/loans",
        json={"member_id": data["inactive"].id, "book_id": data["book"].id, "due_date": DUE_DATE},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_borrow_missing_member_returns_400(client, loan_data):
    resp = client.post(
        "/api/v1/loans",
        json={"member_id": 99999, "book_id": loan_data["book"].id, "due_date": DUE_DATE},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_borrow_missing_book_returns_400(client, loan_data):
    resp = client.post(
        "/api/v1/loans",
        json={"member_id": loan_data["active"].id, "book_id": 99999, "due_date": DUE_DATE},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_borrow_no_copies_available_returns_409(client, loan_data, db):
    """Fill both copies with active loans, then a third borrow should be 409."""
    data = loan_data
    db.add_all([
        Loan(member_id=data["active"].id, book_id=data["book"].id,
             loan_date=date.today(), due_date=date.today() + timedelta(days=14)),
        Loan(member_id=data["active"].id, book_id=data["book"].id,
             loan_date=date.today(), due_date=date.today() + timedelta(days=14)),
    ])
    db.commit()

    resp = client.post(
        "/api/v1/loans",
        json={"member_id": data["active"].id, "book_id": data["book"].id, "due_date": DUE_DATE},
        headers=HEADERS,
    )
    assert resp.status_code == 409


def test_borrow_missing_api_key_returns_401(client, loan_data):
    data = loan_data
    resp = client.post(
        "/api/v1/loans",
        json={"member_id": data["active"].id, "book_id": data["book"].id, "due_date": DUE_DATE},
    )
    assert resp.status_code == 401


# ── Return flow ───────────────────────────────────────────────

def test_return_sets_return_date(client, loan_data, db):
    data = loan_data
    loan = Loan(
        member_id=data["active"].id,
        book_id=data["book"].id,
        loan_date=date.today(),
        due_date=date.today() + timedelta(days=14),
    )
    db.add(loan)
    db.commit()

    resp = client.post(f"/api/v1/loans/{loan.id}/return", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["return_date"] == str(date.today())


def test_return_already_returned_returns_409(client, loan_data, db):
    data = loan_data
    loan = Loan(
        member_id=data["active"].id,
        book_id=data["book"].id,
        loan_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        return_date=date.today(),               # already returned
    )
    db.add(loan)
    db.commit()

    resp = client.post(f"/api/v1/loans/{loan.id}/return", headers=HEADERS)
    assert resp.status_code == 409


def test_return_missing_loan_returns_404(client, loan_data):
    resp = client.post("/api/v1/loans/99999/return", headers=HEADERS)
    assert resp.status_code == 404