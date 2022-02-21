"""drivers/base_classes.py

Base class for drivers.
"""

import contextlib
import functools
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import (Any, Callable, Dict, List, Mapping, Optional, Sequence,
                    Tuple, TypeVar, Union)

KeysType = Mapping[str, str]
MultiValueKeysType = Mapping[str, Union[str, List[str]]]
Number = TypeVar('Number', int, float)
T = TypeVar('T')


def requires_connection(
    fun: Callable[..., T] = None, *,
    verify: bool = True
) -> Union[Callable[..., T], functools.partial]:
    if fun is None:
        return functools.partial(requires_connection, verify=verify)

    @functools.wraps(fun)
    def inner(self: MetaStore, *args: Any, **kwargs: Any) -> T:
        assert fun is not None
        with self.connect(verify=verify):
            return fun(self, *args, **kwargs)

    return inner


class MetaStore(ABC):
    """Abstract base class for all Terracotta metadata backends.

    Defines a common interface for all metadata backends.
    """
    _RESERVED_KEYS = ('limit', 'page')

    @property
    @abstractmethod
    def db_version(self) -> str:
        """Terracotta version used to create the database."""
        pass

    @property
    @abstractmethod
    def key_names(self) -> Tuple[str, ...]:
        """Names of all keys defined by the database."""
        pass

    @abstractmethod
    def __init__(self, url_or_path: str) -> None:
        self.path = url_or_path

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        """Convert given path to normalized version (that can be used for caching)"""
        return path

    @abstractmethod
    def create(self, keys: Sequence[str], *,
               key_descriptions: Mapping[str, str] = None) -> None:
        """Create a new, empty database"""
        pass

    @abstractmethod
    def connect(self, verify: bool = True) -> contextlib.AbstractContextManager:
        """Context manager to connect to a given database and clean up on exit.

        This allows you to pool interactions with the database to prevent possibly
        expensive reconnects, or to roll back several interactions if one of them fails.
        """
        pass

    @abstractmethod
    def get_keys(self) -> OrderedDict:
        """Get all known keys and their fulltext descriptions."""
        pass

    @abstractmethod
    def get_datasets(self, where: MultiValueKeysType = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], Any]:
        """Get all known dataset key combinations matching the given constraints,
        and a path to retrieve the data
        """
        pass

    @abstractmethod
    def get_metadata(self, keys: KeysType) -> Optional[Dict[str, Any]]:
        """Return all stored metadata for given keys."""
        pass

    @abstractmethod
    def insert(self, keys: KeysType, path: str, *, metadata: Mapping[str, Any] = None) -> None:
        """Register a new dataset. This also populates the metadata database,
        if metadata is specified and not `None`."""
        pass

    @abstractmethod
    def delete(self, keys: KeysType) -> None:
        """Remove a dataset, including information from the metadata database."""
        pass

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(\'{self.path}\')'


class RasterStore(ABC):
    """Abstract base class for all Terracotta raster backends.

    Defines a common interface for all raster backends."""

    @abstractmethod
    # TODO: add accurate signature if mypy ever supports conditional return types
    def get_raster_tile(self, path: str, *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        """Load a raster tile with given path and bounds."""
        pass

    @abstractmethod
    def compute_metadata(self, path: str, *,
                         extra_metadata: Any = None,
                         use_chunks: bool = None,
                         max_shape: Sequence[int] = None) -> Dict[str, Any]:
        """Compute metadata for a given input file"""
        pass

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'
