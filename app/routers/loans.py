from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, Loan, Member
from app.schemas import LoanCreate, LoanResponse, Paginated

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])


# POST /api/v1/loans — borrow a book
@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def borrow_book(payload: LoanCreate, db: Session = Depends(get_db)):
    # Member must exist.
    member = db.get(Member, payload.member_id)
    if member is None:
        raise HTTPException(
            status_code=400,
            detail=f"Member {payload.member_id} does not exist",
        )

    # BRIEF: member must be active.
    if not member.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Member {payload.member_id} is not active",
        )

    # Book must exist.
    book = db.get(Book, payload.book_id)
    if book is None:
        raise HTTPException(
            status_code=400,
            detail=f"Book {payload.book_id} does not exist",
        )

    active_loan_count = (
        db.query(Loan)
        .filter(Loan.book_id == payload.book_id, Loan.return_date.is_(None))
        .count()
    )
    if active_loan_count >= book.total_copies:
        raise HTTPException(
            status_code=409,
            detail=(
                f"No copies of book {payload.book_id} are available "
                f"({active_loan_count}/{book.total_copies} already on loan)"
            ),
        )

    loan = Loan(
        member_id=payload.member_id,
        book_id=payload.book_id,
        loan_date=date.today(),
        due_date=payload.due_date,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


# POST /api/v1/loans/{id}/return — return a borrowed book
@router.post("/{loan_id}/return", response_model=LoanResponse)
def return_book(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    # BRIEF: if already returned, return 409.
    if loan.return_date is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Loan {loan_id} was already returned on {loan.return_date}",
        )

    loan.return_date = date.today()
    db.commit()
    db.refresh(loan)
    return loan


# GET /api/v1/loans — list with filters and pagination
@router.get("", response_model=Paginated[LoanResponse])
def list_loans(
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
    status: Optional[Literal["active", "returned", "overdue"]] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    today = date.today()
    query = db.query(Loan)

    if member_id is not None:
        query = query.filter(Loan.member_id == member_id)

    if book_id is not None:
        query = query.filter(Loan.book_id == book_id)

    if status == "active":
        query = query.filter(Loan.return_date.is_(None), Loan.due_date >= today)
    elif status == "returned":
        query = query.filter(Loan.return_date.is_not(None))
    elif status == "overdue":
        query = query.filter(Loan.return_date.is_(None), Loan.due_date < today)

    # Count (after filters, before pagination) for the total field.
    total = query.count()

    # Apply pagination last.
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Paginated[LoanResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )