from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, Loan, Member
from app.schemas import OverdueLoanItem, TopBorrowerItem

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# GET /api/v1/reports/top-borrowers
@router.get("/top-borrowers", response_model=List[TopBorrowerItem])
def top_borrowers(
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Top N members by total number of loans (returned and active combined)."""
    rows = (
        db.query(
            Member.id,
            Member.full_name,
            Member.email,
            func.count(Loan.id).label("total_loans"),
        )
        .join(Loan, Loan.member_id == Member.id)     # JOIN members → loans
        .group_by(Member.id)
        .order_by(func.count(Loan.id).desc())        # most loans first
        .limit(limit)
        .all()
    )

    return [
        TopBorrowerItem(
            id=row.id,
            full_name=row.full_name,
            email=row.email,
            total_loans=row.total_loans,
        )
        for row in rows
    ]


# GET /api/v1/reports/overdue-loans
@router.get("/overdue-loans", response_model=List[OverdueLoanItem])
def overdue_loans(db: Session = Depends(get_db)):
    """All active loans where due_date is in the past."""
    today = date.today()

    rows = (
        db.query(
            Loan.id.label("loan_id"),
            Member.full_name.label("member_name"),
            Book.title.label("book_title"),
            Loan.due_date,
        )
        .join(Member, Member.id == Loan.member_id)   # JOIN loans → members
        .join(Book, Book.id == Loan.book_id)         # JOIN loans → books
        .filter(Loan.return_date.is_(None))          # not yet returned
        .filter(Loan.due_date < today)               # past their due date
        .order_by(Loan.due_date.asc())               # most overdue first
        .all()
    )

    # days_overdue is calculated in Python — simpler and
    # more portable than using SQLite-specific date functions.
    return [
        OverdueLoanItem(
            loan_id=row.loan_id,
            member_name=row.member_name,
            book_title=row.book_title,
            due_date=row.due_date,
            days_overdue=(today - row.due_date).days,
        )
        for row in rows
    ]