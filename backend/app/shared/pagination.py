from typing import Sequence, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    meta: PageMeta
