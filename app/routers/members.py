"""CRUD endpoints for the Members resource."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Loan, Member
from app.schemas import (
    MemberCreate,
    MemberResponse,
    MemberUpdate,
    Paginated,
)

router = APIRouter(prefix="/api/v1/members", tags=["members"])


# GET /api/v1/members — list (paginated)
@router.get("", response_model=Paginated[MemberResponse])
def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Member).count()
    items = db.query(Member).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Paginated[MemberResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


# GET /api/v1/members/{id} — retrieve one
@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


# POST /api/v1/members — create
@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    # Uniqueness pre-check on email
    existing = db.query(Member).filter(Member.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Member with email '{payload.email}' already exists",
        )

    member = Member(
        full_name=payload.full_name,
        email=payload.email,
        is_active=payload.is_active,
    )
    
    if payload.join_date is not None:
        member.join_date = payload.join_date

    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# PATCH /api/v1/members/{id} — update
@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    if payload.full_name is not None:
        member.full_name = payload.full_name
    if payload.email is not None:
        # Uniqueness check against OTHER members
        existing = db.query(Member).filter(
            Member.email == payload.email,
            Member.id != member_id,
        ).first()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Member with email '{payload.email}' already exists",
            )
        member.email = payload.email
    if payload.join_date is not None:
        member.join_date = payload.join_date
    if payload.is_active is not None:
        member.is_active = payload.is_active

    db.commit()
    db.refresh(member)
    return member


# DELETE /api/v1/members/{id}
@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    active_loan_count = (
        db.query(Loan)
        .filter(Loan.member_id == member_id, Loan.return_date.is_(None))
        .count()
    )
    if active_loan_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete member: {active_loan_count} active loan(s) outstanding",
        )

    try:
        db.delete(member)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete member: loan history exists",
        )