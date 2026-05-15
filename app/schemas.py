from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from datetime import date
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")

class Paginated(BaseModel, Generic[T]):

    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int

# ============================================================
# Categories
# ============================================================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Authors
# ============================================================

class AuthorBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=1, max_length=100)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    country: Optional[str] = Field(None, min_length=1, max_length=100)


class AuthorResponse(AuthorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Members
# ============================================================

class MemberBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr


class MemberCreate(MemberBase):
    join_date: Optional[date] = None
    is_active: bool = True


class MemberUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    join_date: Optional[date] = None
    is_active: Optional[bool] = None


class MemberResponse(MemberBase):
    id: int
    join_date: date
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Books
# ============================================================

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    isbn: str = Field(..., min_length=10, max_length=20)
    total_copies: int = Field(default=1, ge=0)
    published_year: int = Field(..., ge=1000, le=2100)


class BookCreate(BookBase):
    category_id: int
    author_ids: List[int] = Field(..., min_length=1)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    total_copies: Optional[int] = Field(None, ge=0)
    published_year: Optional[int] = Field(None, ge=1000, le=2100)
    category_id: Optional[int] = None
    author_ids: Optional[List[int]] = Field(None, min_length=1)


class BookResponse(BookBase):
    id: int
    category: CategoryResponse
    authors: List[AuthorResponse]
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Loans
# ============================================================

class LoanCreate(BaseModel):
    member_id: int
    book_id: int
    due_date: date


class LoanResponse(BaseModel):
    id: int
    member_id: int
    book_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Reports
# ============================================================

class TopBorrowerItem(BaseModel):
    id: int
    full_name: str
    email: str
    total_loans: int
    model_config = ConfigDict(from_attributes=True)


class OverdueLoanItem(BaseModel):
    loan_id: int
    member_name: str
    book_title: str
    due_date: date
    days_overdue: int
    model_config = ConfigDict(from_attributes=True)