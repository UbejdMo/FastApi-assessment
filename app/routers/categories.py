"""CRUD endpoints for the Categories resource."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    Paginated,
)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


# GET /api/v1/categories — list (paginated)
@router.get("", response_model=Paginated[CategoryResponse])
def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Category).count()
    items = db.query(Category).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Paginated[CategoryResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


# GET /api/v1/categories/{id} — retrieve one
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# POST /api/v1/categories — create
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Category '{payload.name}' already exists")

    category = Category(name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# PATCH /api/v1/categories/{id} — update
@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.name is not None:
        existing = db.query(Category).filter(
            Category.name == payload.name,
            Category.id != category_id,
        ).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"Category '{payload.name}' already exists")
        category.name = payload.name

    db.commit()
    db.refresh(category)
    return category


# DELETE /api/v1/categories/{id}
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()