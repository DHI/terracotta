"""concurrency.py

Tools for dealing with concurrent and parallel execution.
"""

from typing import Any, Iterable
import functools
from concurrent.futures import ProcessPoolExecutor, Future


class LazyProcessPoolExecutor(ProcessPoolExecutor):
    """Lazy version of ProcessPoolExecutor that forks the first time it is used."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__init_args__ = (args, kwargs)
        self.__initialized__ = False

    def __sup_init__(self) -> None:
        if self.__initialized__:
            return

        init_args, init_kwargs = self.__init_args__
        super().__init__(*init_args, **init_kwargs)
        self.__initialized__ = True

    @functools.wraps(ProcessPoolExecutor.submit)
    def submit(self, *args: Any, **kwargs: Any) -> Future:
        self.__sup_init__()
        return super().submit(*args, **kwargs)

    @functools.wraps(ProcessPoolExecutor.map)
    def map(self, *args: Any, **kwargs: Any) -> Iterable[Any]:
        self.__sup_init__()
        return super().map(*args, **kwargs)

    @functools.wraps(ProcessPoolExecutor.shutdown)
    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        if not self.__initialized__:
            return
        return super().shutdown(*args, **kwargs)
