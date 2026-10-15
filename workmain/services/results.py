"""
Result types shared by service-layer collection queries.
"""

from dataclasses import dataclass
from typing import Generic, Tuple, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    """The result of a collection query.

    Attributes:
        rows: The rows returned, after any cap.
        total: Every match, before any cap.
        filters: The filters that narrowed the query, as (name, value) pairs.
            A filter that narrows nothing, such as status 'all', is absent.
    """

    rows: Tuple[T, ...]
    total: int
    filters: Tuple[Tuple[str, object], ...] = ()
