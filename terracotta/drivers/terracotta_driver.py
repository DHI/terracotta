"""drivers/terracotta_driver.py

The driver to interact with.
"""

import contextlib
from collections import OrderedDict
from typing import (Any, Collection, Dict, List, Mapping, Optional, Sequence, Tuple, TypeVar,
                    Union)

import terracotta
from terracotta import exceptions
from terracotta.drivers.base_classes import (KeysType, MetaStore,
                                             MultiValueKeysType, RasterStore,
                                             requires_connection)

ExtendedKeysType = Union[Sequence[str], Mapping[str, str]]
ExtendedMultiValueKeysType = Union[Sequence[str], Mapping[str, Union[str, List[str]]]]
T = TypeVar('T')


def squeeze(iterable: Collection[T]) -> T:
    assert len(iterable) == 1
    return next(iter(iterable))


class TerracottaDriver:
    """Terracotta driver object used to retrieve raster tiles and metadata.

    Do not instantiate directly, use :func:`terracotta.get_driver` instead.
    """
    def __init__(self, meta_store: MetaStore, raster_store: RasterStore) -> None:
        self.meta_store = meta_store
        self.raster_store = raster_store

        settings = terracotta.get_settings()
        self.LAZY_LOADING_MAX_SHAPE: Tuple[int, int] = settings.LAZY_LOADING_MAX_SHAPE

    @property
    def db_version(self) -> str:
        """Terracotta version used to create the meta store.

        Returns:

            A str specifying the version of Terracotta that was used to create the meta store.

        """
        return self.meta_store.db_version

    @property
    def key_names(self) -> Tuple[str, ...]:
        """Get names of all keys defined by the meta store.

        Returns:

            A tuple defining the key names and order.

        """
        return self.meta_store.key_names

    def create(self, keys: Sequence[str], *,
               key_descriptions: Mapping[str, str] = None) -> None:
        """Create a new, empty metadata store.

        Arguments:

            keys: A sequence defining the key names and order.
            key_descriptions: A mapping from key name to a human-readable
                description of what the key encodes.

        """
        self.meta_store.create(keys=keys, key_descriptions=key_descriptions)

    def connect(self, verify: bool = True) -> contextlib.AbstractContextManager:
        """Context manager to connect to the metastore and clean up on exit.

        This allows you to pool interactions with the metastore to prevent possibly
        expensive reconnects, or to roll back several interactions if one of them fails.

        Arguments:

            verify: Whether to verify the metastore (primarily its version) when connecting.
                Should be `true` unless absolutely necessary, such as when instantiating the
                metastore during creation of it.

        Note:

            Make sure to call :meth:`create` on a fresh metastore before using this method.

        Example:

            >>> import terracotta as tc
            >>> driver = tc.get_driver('tc.sqlite')
            >>> with driver.connect():
            ...     for keys, dataset in datasets.items():
            ...         # connection will be kept open between insert operations
            ...         driver.insert(keys, dataset)

        """
        return self.meta_store.connect(verify=verify)

    @requires_connection
    def get_keys(self) -> OrderedDict:
        """Get all known keys and their fulltext descriptions.

        Returns:

            An :class:`~collections.OrderedDict` in the form
            ``{key_name: key_description}``

        """
        return self.meta_store.get_keys()

    @requires_connection
    def get_datasets(self, where: MultiValueKeysType = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], Any]:
        """Get all known dataset key combinations matching the given constraints,
        and a path to retrieve the data (dependent on the raster store).

        Arguments:

            where: A mapping from key name to key value constraint(s)
            page: A pagination parameter, skips first page * limit results
            limit: A pagination parameter, max number of results to return

        Returns:

            A :class:`dict` mapping from key sequence tuple to dataset path.

        """
        return self.meta_store.get_datasets(
            where=self._standardize_multi_value_keys(where, requires_all_keys=False),
            page=page,
            limit=limit
        )

    @requires_connection
    def get_metadata(self, keys: ExtendedKeysType) -> Dict[str, Any]:
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
        keys = self._standardize_keys(keys)

        metadata = self.meta_store.get_metadata(keys)

        if metadata is None:
            # metadata is not computed yet, trigger lazy loading
            dataset = self.get_datasets(keys)
            if not dataset:
                raise exceptions.DatasetNotFoundError('No dataset found')

            path = squeeze(dataset.values())
            metadata = self.compute_metadata(path, max_shape=self.LAZY_LOADING_MAX_SHAPE)
            self.insert(keys, path, metadata=metadata)

            # ensure standardized/consistent output (types and floating point precision)
            metadata = self.meta_store.get_metadata(keys)
            assert metadata is not None

        return metadata

    @requires_connection
    def insert(
        self, keys: ExtendedKeysType,
        path: str, *,
        override_path: str = None,
        metadata: Mapping[str, Any] = None,
        skip_metadata: bool = False
    ) -> None:
        """Register a new dataset. Used to populate meta store.

        Arguments:

            keys: Keys of the dataset. Can either be given as a sequence of key values, or
                as a mapping ``{key_name: key_value}``.
            path: Path to access dataset (driver dependent).
            override_path: If given, this path will be inserted into the meta store
                instead of the one used to load the dataset.
            metadata: Metadata dict for the dataset. If not given, metadata will be computed
                via :meth:`compute_metadata`.
            skip_metadata: If True, will skip metadata computation (will be computed
                during first request instead). Has no effect if ``metadata`` argument is given.

        """
        keys = self._standardize_keys(keys)

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(path)

        self.meta_store.insert(
            keys=keys,
            path=override_path or path,
            metadata=metadata
        )

    @requires_connection
    def delete(self, keys: ExtendedKeysType) -> None:
        """Remove a dataset from the meta store.

        Arguments:

            keys:  Keys of the dataset. Can either be given as a sequence of key values, or
                as a mapping ``{key_name: key_value}``.

        """
        keys = self._standardize_keys(keys)

        self.meta_store.delete(keys)

    def get_raster_tile(self, keys: ExtendedKeysType, *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        """Load a raster tile with given keys and bounds.

        Arguments:

            keys: Key sequence identifying the dataset to load tile from.
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
        path = squeeze(self.get_datasets(keys).values())

        return self.raster_store.get_raster_tile(
            path=path,
            tile_bounds=tile_bounds,
            tile_size=tile_size,
            preserve_values=preserve_values,
            asynchronous=asynchronous,
        )

    def compute_metadata(self, path: str, *,
                         extra_metadata: Any = None,
                         use_chunks: bool = None,
                         max_shape: Sequence[int] = None) -> Dict[str, Any]:
        """Compute metadata for a dataset.

        Arguments:

            path: Path identifing the dataset.
            extra_metadata: Any additional metadata that will be returned as is
                in the result, under the `metadata` key.
            use_chunks: Whether to load the dataset in chunks, when computing.
                Useful if the dataset is too large to fit in memory.
                Mutually exclusive with `max_shape`.
            max_shape: If dataset is larger than this shape, it will be downsampled
                while loading. Useful if the dataset is too large to fit in memory.
                Mutually exclusive with `use_chunks`.

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
        return self.raster_store.compute_metadata(
            path=path,
            extra_metadata=extra_metadata,
            use_chunks=use_chunks,
            max_shape=max_shape,
        )

    def _standardize_keys(
        self, keys: ExtendedKeysType, requires_all_keys: bool = True
    ) -> KeysType:
        return self._ensure_keys_as_dict(keys, requires_all_keys)

    def _standardize_multi_value_keys(
        self, keys: Optional[ExtendedMultiValueKeysType], requires_all_keys: bool = True
    ) -> MultiValueKeysType:
        return self._ensure_keys_as_dict(keys, requires_all_keys)

    def _ensure_keys_as_dict(
        self,
        keys: Union[ExtendedKeysType, Optional[MultiValueKeysType]],
        requires_all_keys: bool = True
    ) -> Dict[str, Any]:
        if requires_all_keys and (keys is None or len(keys) != len(self.key_names)):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        if isinstance(keys, Mapping):
            keys = dict(keys.items())
        elif isinstance(keys, Sequence):
            keys = dict(zip(self.key_names, keys))
        elif keys is None:
            keys = {}
        else:
            raise exceptions.InvalidKeyError(
                'Encountered unknown key type, expected Mapping or Sequence'
            )

        unknown_keys = set(keys) - set(self.key_names)
        if unknown_keys:
            raise exceptions.InvalidKeyError(
                f'Encountered unrecognized keys {unknown_keys} (available keys: {self.key_names})'
            )

        return keys

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(\n'
            f'    meta_store={self.meta_store!r},\n'
            f'    raster_store={self.raster_store!r}\n'
            ')'
        )
