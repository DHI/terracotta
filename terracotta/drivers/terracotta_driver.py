"""drivers/terracotta_driver.py

The driver to interact with.
"""

import contextlib
from collections import OrderedDict
from typing import (Any, Collection, Dict, Mapping, Sequence, Tuple, TypeVar,
                    Union)

import terracotta
from terracotta import exceptions
from terracotta.drivers.base_classes import (KeysType, MetaStore,
                                             MultiValueKeysType, RasterStore,
                                             requires_connection)

ExtendedKeysType = Union[Sequence[str], KeysType]
T = TypeVar('T')


def only_element(iterable: Collection[T]) -> T:
    if not iterable:
        raise exceptions.DatasetNotFoundError('No dataset found')
    assert len(iterable) == 1
    return next(iter(iterable))


class TerracottaDriver:

    def __init__(self, meta_store: MetaStore, raster_store: RasterStore) -> None:
        self.meta_store = meta_store
        self.raster_store = raster_store

        settings = terracotta.get_settings()
        self.LAZY_LOADING_MAX_SHAPE: Tuple[int, int] = settings.LAZY_LOADING_MAX_SHAPE

    @property
    def db_version(self) -> str:
        return self.meta_store.db_version

    @property
    def key_names(self) -> Tuple[str, ...]:
        return self.meta_store.key_names

    def create(self, keys: Sequence[str], *,
               key_descriptions: Mapping[str, str] = None) -> None:
        self.meta_store.create(keys=keys, key_descriptions=key_descriptions)

    def connect(self, verify: bool = True) -> contextlib.AbstractContextManager:
        return self.meta_store.connect(verify=verify)

    @requires_connection
    def get_keys(self) -> OrderedDict:
        return self.meta_store.get_keys()

    @requires_connection
    def get_datasets(self, keys: MultiValueKeysType = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], Any]:
        return self.meta_store.get_datasets(
            where=keys,
            page=page,
            limit=limit
        )

    @requires_connection
    def get_metadata(self, keys: ExtendedKeysType) -> Dict[str, Any]:
        keys = self._standardize_keys(keys)

        metadata = self.meta_store.get_metadata(keys)

        if metadata is None:
            # metadata is not computed yet, trigger lazy loading
            handle = only_element(self.get_datasets(keys).values())
            metadata = self.compute_metadata(handle, max_shape=self.LAZY_LOADING_MAX_SHAPE)
            self.insert(keys, handle, metadata=metadata)

            # this is necessary to make the lazy loading tests pass...
            metadata = self.meta_store.get_metadata(keys)
            assert metadata is not None

        return metadata

    @requires_connection
    def insert(
        self, keys: ExtendedKeysType,
        handle: Any, *,
        override_path: str = None,
        metadata: Mapping[str, Any] = None,
        skip_metadata: bool = False,
        **kwargs: Any
    ) -> None:
        keys = self._standardize_keys(keys)

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(handle)

        self.meta_store.insert(
            keys=keys,
            handle=override_path or handle,
            metadata=metadata,
            **kwargs
        )

    @requires_connection
    def delete(self, keys: ExtendedKeysType) -> None:
        keys = self._standardize_keys(keys)

        self.meta_store.delete(keys)

    def get_raster_tile(self, keys: ExtendedKeysType, *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        handle = only_element(self.get_datasets(keys).values())

        return self.raster_store.get_raster_tile(
            handle=handle,
            tile_bounds=tile_bounds,
            tile_size=tile_size,
            preserve_values=preserve_values,
            asynchronous=asynchronous,
        )

    def compute_metadata(self, handle: str, *,
                         extra_metadata: Any = None,
                         use_chunks: bool = None,
                         max_shape: Sequence[int] = None) -> Dict[str, Any]:
        return self.raster_store.compute_metadata(
            handle=handle,
            extra_metadata=extra_metadata,
            use_chunks=use_chunks,
            max_shape=max_shape,
        )

    def _standardize_keys(
        self,
        keys: ExtendedKeysType,
        requires_all_keys: bool = True
    ) -> KeysType:
        if requires_all_keys and (keys is None or len(keys) != len(self.key_names)):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        if isinstance(keys, Mapping):
            keys = dict(keys.items())
        elif isinstance(keys, Sequence):
            keys = dict(zip(self.key_names, keys))
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
        return self.meta_store.__repr__()
