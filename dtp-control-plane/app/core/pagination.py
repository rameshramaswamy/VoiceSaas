from fastapi import Query
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PageParams:
    """Dependency for Query Parameters"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.size = size
        self.skip = (page - 1) * size

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard Response Envelope"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

def paginate(items: List[T], total: int, params: PageParams) -> PaginatedResponse[T]:
    import math
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=math.ceil(total / params.size)
    )