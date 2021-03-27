from collections.abc import Iterable
from typing import Callable, Optional, TypeVar


T = TypeVar("T")


def first_where(
    condition: Callable[[T], bool],
    it: Iterable[T],
    /,
) -> Optional[T]:
    return next(filter(condition, it), None)
