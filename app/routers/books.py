from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.models import Author, Book, Category, Loan, book_authors
from app.schemas import BookCreate, BookResponse, BookUpdate, Paginated

router = APIRouter(prefix="/api/v1/books", tags=["books"])


# -------- helpers ---------------------------------------------

def _validate_category(db: Session, category_id: int) -> None:
    """Raise 400 if the category doesn't exist."""
    if db.get(Category, category_id) is None:
        raise HTTPException(
            status_code=400,
            detail=f"Category {category_id} does not exist",
        )


def _resolve_authors(db: Session, author_ids: list[int]) -> list[Author]:
    """Return Author objects for the given IDs, or raise 400 if any are missing."""
    authors = db.query(Author).filter(Author.id.in_(author_ids)).all()
    if len(authors) != len(set(author_ids)):
        found = {a.id for a in authors}
        missing = sorted(set(author_ids) - found)
        raise HTTPException(
            status_code=400,
            detail=f"Author(s) not found: {missing}",
        )
    return authors


# -------- endpoints -------------------------------------------

# GET /api/v1/books/search — filtered, sorted, paginated
# MUST be declared before /{book_id} or FastAPI will try to parse "search" as an int.
@router.get("/search", response_model=Paginated[BookResponse])
def search_books(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    author_id: Optional[int] = None,
    available_only: bool = False,
    published_after: Optional[int] = None,
    published_before: Optional[int] = None,
    sort_by: Literal["title", "published_year", "popularity"] = "title",
    sort_order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # ── Build the base query, then layer filters on top ──────────────

    query = db.query(Book)

    # Free-text title match (case-insensitive partial match).
    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))

    # Filter by category.
    if category_id is not None:
        query = query.filter(Book.category_id == category_id)

    # Filter by author — uses the M:N relationship via a subquery.
    # We use IN(...) instead of a JOIN to avoid row multiplication
    # (a book with 3 authors would appear 3 times with a direct JOIN).
    if author_id is not None:
        query = query.filter(
            Book.id.in_(
                db.query(book_authors.c.book_id)
                .filter(book_authors.c.author_id == author_id)
            )
        )

    # Filter to only books with at least one copy currently available.
    # available = total_copies > count of active (unreturned) loans for this book.
    if available_only:
        active_loans_for_book = (
            db.query(func.count(Loan.id))
            .filter(Loan.book_id == Book.id, Loan.return_date.is_(None))
            .correlate(Book)
            .scalar_subquery()
        )
        query = query.filter(Book.total_copies > active_loans_for_book)

    # Year range filters.
    if published_after is not None:
        query = query.filter(Book.published_year >= published_after)

    if published_before is not None:
        query = query.filter(Book.published_year <= published_before)

    # ── Sort ─────────────────────────────────────────────────────────

    if sort_by == "popularity":
        # Popularity = total all-time loans for this book (returned + active).
        # Correlated subquery: runs once per book row, clean with no JOIN issues.
        total_loans_for_book = (
            db.query(func.count(Loan.id))
            .filter(Loan.book_id == Book.id)
            .correlate(Book)
            .scalar_subquery()
        )
        order_col = (
            total_loans_for_book.desc()
            if sort_order == "desc"
            else total_loans_for_book.asc()
        )
    elif sort_by == "published_year":
        order_col = (
            Book.published_year.desc()
            if sort_order == "desc"
            else Book.published_year.asc()
        )
    else:  # default: title
        order_col = (
            Book.title.desc()
            if sort_order == "desc"
            else Book.title.asc()
        )

    # ── Count (before pagination, same filters as above) ─────────────

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # ── Items (with eager loading, ordering, and pagination) ──────────

    items = (
        query
        .options(
            joinedload(Book.category),     # M:1 — single JOIN to categories
            selectinload(Book.authors),    # M:N — one IN-query for all authors
        )
        .order_by(order_col)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return Paginated[BookResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )

# GET /api/v1/books — list (paginated)
@router.get("", response_model=Paginated[BookResponse])
def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Book).count()
    items = (
        db.query(Book)
        .options(
            joinedload(Book.category),       # M:1 — single JOIN, no row multiplication
            selectinload(Book.authors),      # M:N — separate IN-query, avoids N+1
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Paginated[BookResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


# GET /api/v1/books/{id} — retrieve one
@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = (
        db.query(Book)
        .options(joinedload(Book.category), selectinload(Book.authors))
        .filter(Book.id == book_id)
        .first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# POST /api/v1/books — create
@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    # ISBN uniqueness pre-check
    if db.query(Book).filter(Book.isbn == payload.isbn).first() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Book with ISBN '{payload.isbn}' already exists",
        )

    _validate_category(db, payload.category_id)
    authors = _resolve_authors(db, payload.author_ids)

    book = Book(
        title=payload.title,
        isbn=payload.isbn,
        total_copies=payload.total_copies,
        published_year=payload.published_year,
        category_id=payload.category_id,
    )
    book.authors = authors            # SQLAlchemy auto-inserts rows in book_authors
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


# PATCH /api/v1/books/{id} — update
@router.patch("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if payload.title is not None:
        book.title = payload.title

    if payload.isbn is not None:
        existing = db.query(Book).filter(
            Book.isbn == payload.isbn,
            Book.id != book_id,
        ).first()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Book with ISBN '{payload.isbn}' already exists",
            )
        book.isbn = payload.isbn

    if payload.total_copies is not None:
        book.total_copies = payload.total_copies

    if payload.published_year is not None:
        book.published_year = payload.published_year

    if payload.category_id is not None:
        _validate_category(db, payload.category_id)
        book.category_id = payload.category_id

    if payload.author_ids is not None:
        book.authors = _resolve_authors(db, payload.author_ids)

    db.commit()
    db.refresh(book)
    return book


# DELETE /api/v1/books/{id}
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Brief: cannot delete a book with active loans → 409.
    active_loan_count = (
        db.query(Loan)
        .filter(Loan.book_id == book_id, Loan.return_date.is_(None))
        .count()
    )
    if active_loan_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete book: {active_loan_count} active loan(s) outstanding",
        )

    # Returned loans (loan history) still reference this book via FK → catch IntegrityError.
    try:
        db.delete(book)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete book: loan history exists",
        )