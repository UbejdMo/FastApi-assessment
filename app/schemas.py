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