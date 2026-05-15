"""Tests for the book search endpoint: filters, pagination, and sort."""

import pytest
from datetime import date
from app.models import Author, Book, Category, Loan, Member


def _add_book(db, title, isbn, category, author, year, copies=1):
    book = Book(
        title=title, isbn=isbn,
        category_id=category.id,
        total_copies=copies,
        published_year=year,
    )
    book.authors = [author]
    db.add(book)
    db.commit()
    return book


@pytest.fixture
def search_data(db):
    """Four books across two categories and two authors for predictable assertions."""
    cat1 = Category(name="Fiction")
    cat2 = Category(name="Science")
    db.add_all([cat1, cat2])
    db.commit()

    a1 = Author(full_name="Alice Writer", country="Albania")
    a2 = Author(full_name="Bob Author", country="Kosovo")
    db.add_all([a1, a2])
    db.commit()

    b1 = _add_book(db, "The Great Adventure", "978-0-000-00001-0", cat1, a1, 1990, copies=2)
    b2 = _add_book(db, "Science Today",       "978-0-000-00002-0", cat2, a2, 2010)
    b3 = _add_book(db, "Adventure in Space",  "978-0-000-00003-0", cat1, a1, 2020)
    b4 = _add_book(db, "Modern Science",      "978-0-000-00004-0", cat2, a2, 2015)

    member = Member(full_name="Reader", email="r@test.com",
                    join_date=date.today(), is_active=True)
    db.add(member)
    db.commit()

    # Give b1 two loans (highest popularity)
    for _ in range(2):
        loan = Loan(member_id=member.id, book_id=b1.id,
                    loan_date=date.today(), due_date=date(2030, 1, 1),
                    return_date=date.today())
        db.add(loan)
    db.commit()

    return dict(cat1=cat1, cat2=cat2, a1=a1, a2=a2,
                b1=b1, b2=b2, b3=b3, b4=b4, member=member)


def test_search_no_filters_returns_all(client, search_data):
    resp = client.get("/api/v1/books/search")
    assert resp.status_code == 200
    assert resp.json()["total"] == 4


def test_search_pagination_shape(client, search_data):
    """Response always has items, page, page_size, total, total_pages."""
    resp = client.get("/api/v1/books/search?page=1&page_size=2")
    body = resp.json()
    assert resp.status_code == 200
    for key in ("items", "page", "page_size", "total", "total_pages"):
        assert key in body
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] == 4
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2


def test_search_page_beyond_total_returns_empty(client, search_data):
    """page > total_pages returns empty items, not an error."""
    resp = client.get("/api/v1/books/search?page=99")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 4              # total count unchanged


def test_search_q_partial_match(client, search_data):
    """q matches partial title, case-insensitively."""
    resp = client.get("/api/v1/books/search?q=adventure")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2      # "The Great Adventure" + "Adventure in Space"


def test_search_category_filter(client, search_data):
    d = search_data
    resp = client.get(f"/api/v1/books/search?category_id={d['cat1'].id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_search_author_filter_uses_m2n(client, search_data):
    """author_id filter traverses the M:N relationship correctly."""
    d = search_data
    resp = client.get(f"/api/v1/books/search?author_id={d['a2'].id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_search_published_year_range(client, search_data):
    resp = client.get("/api/v1/books/search?published_after=2010&published_before=2015")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2      # 2010 and 2015


def test_search_filter_composition(client, search_data):
    """Multiple filters AND their results — not just the last one."""
    d = search_data
    resp = client.get(
        f"/api/v1/books/search?category_id={d['cat1'].id}&author_id={d['a1'].id}"
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 2     # Fiction books by a1 only


def test_search_sort_title_asc(client, search_data):
    resp = client.get("/api/v1/books/search?sort_by=title&sort_order=asc")
    assert resp.status_code == 200
    titles = [i["title"] for i in resp.json()["items"]]
    assert titles == sorted(titles)


def test_search_sort_popularity_desc(client, search_data):
    """Book with most loans appears first when sorted by popularity desc."""
    d = search_data
    resp = client.get("/api/v1/books/search?sort_by=popularity&sort_order=desc")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == d["b1"].id    # b1 has 2 loans