"""
Pagination schemas for API responses.
"""
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(1, ge=1, description="Page number, starting from 1")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
