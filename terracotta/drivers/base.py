"""drivers/base.py

Base class for drivers.
"""

from typing import Callable, Mapping, Any, Tuple, Sequence, Dict, Union, TypeVar
from abc import ABC, abstractmethod
from collections import OrderedDict
import functools
import contextlib

Number = TypeVar('Number', int, float)
T = TypeVar('T')


def requires_connection(fun: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(fun)
    def inner(self: Driver, *args: Any, **kwargs: Any) -> T:
        with self.connect():
            return fun(self, *args, **kwargs)
    return inner


class Driver(ABC):
    """Abstract base class for all data backends.

    Defines a common interface for all handlers.
    """
    key_names: Tuple[str]

    @abstractmethod
    def __init__(self, url_or_path: str) -> None:
        self.path = url_or_path

    @abstractmethod
    def create(self, keys: Sequence[str], *args: Any,
               key_descriptions: Mapping[str, str] = None, **kwargs: Any) -> None:
        """Create a new, empty data storage"""
        pass

    @abstractmethod
    def connect(self) -> contextlib.AbstractContextManager:
        """Context manager to connect to a given database and clean up on exit."""
        pass

    @abstractmethod
    def get_keys(self) -> OrderedDict:
        """Get all known keys and their fulltext descriptions."""
        pass

    @abstractmethod
    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], Any]:
        """Get all known dataset key combinations matching the given pattern (all if not given).

        Values are a handle to retrieve data.
        """
        pass

    @abstractmethod
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        """Return all stored metadata for given keys.

        Metadata has to contain the following keys:
          - range: global minimum and maximum value in dataset
          - bounds: physical bounds covered by dataset
          - convex_hull: GeoJSON shape specifying total data coverage
          - nodata: data value denoting missing or invalid data
          - percentiles: array of pre-computed percentiles in range(1, 100)
          - mean: global mean
          - stdev: global standard deviation
          - metadata: any additional client-relevant metadata
        """
        pass

    @abstractmethod
    # TODO: add accurate signature if mypy ever supports conditional return types
    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        nodata: Number = 0,
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        """Get raster tile as a NumPy array for given keys and bounds.

        If asynchronous=True, returns a Future containing the result instead.
        """
        pass

    @staticmethod
    @abstractmethod
    def compute_metadata(data: Any, *,
                         extra_metadata: Any = None) -> Dict[str, Any]:
        """Compute metadata for a given input file."""
        pass

    @abstractmethod
    def insert(self, *args: Any,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               **kwargs: Any) -> None:
        """Register a new dataset. Used to populate data storage."""
        pass

    @abstractmethod
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        """Remove a dataset from metadata storage."""
        pass

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(\'{self.path}\')'
