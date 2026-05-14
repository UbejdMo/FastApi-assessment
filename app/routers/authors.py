from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Author
from app.schemas import (
    AuthorCreate,
    AuthorResponse,
    AuthorUpdate,
    Paginated,
)

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])


# GET /api/v1/authors — list (paginated)
@router.get("", response_model=Paginated[AuthorResponse])
def list_authors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Author).count()
    items = db.query(Author).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Paginated[AuthorResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


# GET /api/v1/authors/{id} — retrieve one
@router.get("/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


# POST /api/v1/authors — create
@router.post("", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
def create_author(payload: AuthorCreate, db: Session = Depends(get_db)):
    author = Author(full_name=payload.full_name, country=payload.country)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


# PATCH /api/v1/authors/{id} — update
@router.patch("/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, payload: AuthorUpdate, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    if payload.full_name is not None:
        author.full_name = payload.full_name
    if payload.country is not None:
        author.country = payload.country

    db.commit()
    db.refresh(author)
    return author


# DELETE /api/v1/authors/{id}
@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    db.delete(author)
    db.commit()