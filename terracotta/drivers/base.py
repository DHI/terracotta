"""drivers/base.py

Base class for drivers.
"""

from abc import ABC, abstractmethod
from typing import Callable, Mapping, Any, Tuple, Sequence, Dict, Union, List, TypeVar
import sys
import operator
import math
import warnings
import functools
import contextlib

from cachetools import cachedmethod, LRUCache
import numpy as np

from terracotta import get_settings, exceptions

Number = TypeVar('Number', int, float)


def requires_connection(fun: Callable) -> Callable:
    @functools.wraps(fun)
    def inner(self: Driver, *args: Any, **kwargs: Any) -> Any:
        with self.connect():
            return fun(self, *args, **kwargs)
    return inner


class Driver(ABC):
    """Abstract base class for all data backends.

    Defines a common interface for all handlers.
    """
    available_keys: Tuple[str]

    @abstractmethod
    def __init__(self, url_or_path: str) -> None:
        pass

    @abstractmethod
    def create(self, *args: Any, **kwargs: Any) -> None:
        """Create a new, empty data storage"""
        pass

    @abstractmethod
    def connect(self) -> contextlib.AbstractContextManager:
        """Context manager to connect to a given database and clean up on exit."""
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
          - nodata: data value denoting missing or invalid data
          - percentiles: array of pre-computed percentiles in range(1, 100)
          - mean: global mean
          - stdev: global standard deviation
          - metadata: any additional client-relevant metadata
        """
        pass

    @abstractmethod
    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tilesize: Sequence[int] = (256, 256),
                        nodata: Number = 0) -> np.ndarray:
        """Get raster tile as a NumPy array for given keys."""
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


