"""drivers/base.py

Base class for drivers.
"""

from typing import Callable, List, Mapping, Any, Tuple, Sequence, Dict, Union, TypeVar
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
    """Abstract base class for all Terracotta data backends.

    Defines a common interface for all drivers.
    """
    _RESERVED_KEYS = ('limit', 'page')

    db_version: str  #: Terracotta version used to create the database
    key_names: Tuple[str]  #: Names of all keys defined by the database

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
        # Create a new, empty database (driver dependent)
        pass

    @abstractmethod
    def connect(self) -> contextlib.AbstractContextManager:
        """Context manager to connect to a given database and clean up on exit.

        This allows you to pool interactions with the database to prevent possibly
        expensive reconnects, or to roll back several interactions if one of them fails.

        Note:

            Make sure to call :meth:`create` on a fresh database before using this method.

        Example:

            >>> import terracotta as tc
            >>> driver = tc.get_driver('tc.sqlite')
            >>> with driver.connect():
            ...     for keys, dataset in datasets.items():
            ...         # connection will be kept open between insert operations
            ...         driver.insert(keys, dataset)

        """
        pass

    @abstractmethod
    def get_keys(self) -> OrderedDict:
        """Get all known keys and their fulltext descriptions.

        Returns:

            An :class:`~collections.OrderedDict` in the form
            ``{key_name: key_description}``

        """
        pass

    @abstractmethod
    def get_datasets(self, where: Mapping[str, Union[str, List[str]]] = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], Any]:
        # Get all known dataset key combinations matching the given constraints,
        # and a handle to retrieve the data (driver dependent)
        pass

    @abstractmethod
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        """Return all stored metadata for given keys.

        Arguments:

            keys: Keys of the requested dataset. Can either be given as a sequence of key values,
                or as a mapping ``{key_name: key_value}``.

        Returns:

            A :class:`dict` with the values

            - ``range``: global minimum and maximum value in dataset
            - ``bounds``: physical bounds covered by dataset in latitude-longitude projection
            - ``convex_hull``: GeoJSON shape specifying total data coverage in latitude-longitude
              projection
            - ``percentiles``: array of pre-computed percentiles from 1% through 99%
            - ``mean``: global mean
            - ``stdev``: global standard deviation
            - ``metadata``: any additional client-relevant metadata

        """
        pass

    @abstractmethod
    # TODO: add accurate signature if mypy ever supports conditional return types
    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        """Load a raster tile with given keys and bounds.

        Arguments:

            keys: Keys of the requested dataset. Can either be given as a sequence of key values,
                or as a mapping ``{key_name: key_value}``.
            tile_bounds: Physical bounds of the tile to read, in Web Mercator projection (EPSG3857).
                Reads the whole dataset if not given.
            tile_size: Shape of the output array to return. Must be two-dimensional.
                Defaults to :attr:`~terracotta.config.TerracottaSettings.DEFAULT_TILE_SIZE`.
            preserve_values: Whether to preserve exact numerical values (e.g. when reading
                categorical data). Sets all interpolation to nearest neighbor.
            asynchronous: If given, the tile will be read asynchronously in a separate thread.
                This function will return immediately with a :class:`~concurrent.futures.Future`
                that can be used to retrieve the result.

        Returns:

            Requested tile as :class:`~numpy.ma.MaskedArray` of shape ``tile_size`` if
            ``asynchronous=False``, otherwise a :class:`~concurrent.futures.Future` containing
            the result.

        """
        pass

    @staticmethod
    @abstractmethod
    def compute_metadata(data: Any, *,
                         extra_metadata: Any = None,
                         **kwargs: Any) -> Dict[str, Any]:
        # Compute metadata for a given input file (driver dependent)
        pass

    @abstractmethod
    def insert(self, keys: Union[Sequence[str], Mapping[str, str]],
               handle: Any, **kwargs: Any) -> None:
        """Register a new dataset. Used to populate metadata database.

        Arguments:

            keys: Keys of the dataset. Can either be given as a sequence of key values, or
                as a mapping ``{key_name: key_value}``.
            handle: Handle to access dataset (driver dependent).

        """
        pass

    @abstractmethod
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        """Remove a dataset from the metadata database.

        Arguments:

            keys:  Keys of the dataset. Can either be given as a sequence of key values, or
                as a mapping ``{key_name: key_value}``.

        """
        pass

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(\'{self.path}\')'
