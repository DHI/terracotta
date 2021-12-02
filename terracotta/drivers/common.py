import contextlib
import functools
import json
import re
import urllib.parse as urlparse
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import (Any, Dict, Iterator, List, Mapping, Optional, Sequence,
                    Tuple, Union)

import numpy as np
import sqlalchemy as sqla
import terracotta
from sqlalchemy.engine.base import Connection
from terracotta import exceptions
from terracotta.drivers.base import requires_connection
from terracotta.drivers.raster_base import RasterDriver
from terracotta.profile import trace


class RelationalDriver(RasterDriver, ABC):
    # NOTE: `convert_exceptions` decorators are NOT added yet

    SQL_DATABASE_SCHEME: str  # The database flavour, eg mysql, sqlite, etc
    SQL_DRIVER_TYPE: str  # The actual database driver, eg pymysql, sqlite3, etc
    SQL_KEY_SIZE: int

    SQLA_REAL = functools.partial(sqla.types.Float, precision=8)
    SQLA_TEXT = sqla.types.Text
    SQLA_BLOB = sqla.types.LargeBinary
    _METADATA_COLUMNS: Tuple[Tuple[str, sqla.types.TypeEngine], ...] = (
        ('bounds_north', SQLA_REAL()),
        ('bounds_east', SQLA_REAL()),
        ('bounds_south', SQLA_REAL()),
        ('bounds_west', SQLA_REAL()),
        ('convex_hull', SQLA_TEXT()),
        ('valid_percentage', SQLA_REAL()),
        ('min', SQLA_REAL()),
        ('max', SQLA_REAL()),
        ('mean', SQLA_REAL()),
        ('stdev', SQLA_REAL()),
        ('percentiles', SQLA_BLOB()),
        ('metadata', SQLA_TEXT())
    )

    def __init__(self, path: str) -> None:
        settings = terracotta.get_settings()
        db_connection_timeout: int = settings.DB_CONNECTION_TIMEOUT

        assert self.SQL_DRIVER_TYPE is not None
        self._CONNECTION_PARAMETERS = self._parse_connection_string(path)
        cp = self._CONNECTION_PARAMETERS
        connection_string = f'{cp.scheme}+{self.SQL_DRIVER_TYPE}://{cp.netloc}{cp.path}'

        self.sqla_engine = sqla.create_engine(
            connection_string,
            echo=True,
            future=True,
            connect_args={'timeout': db_connection_timeout}
        )
        self.sqla_metadata = sqla.MetaData()

        self._db_keys: Optional[OrderedDict] = None

        self.connection: Connection
        self.connected: bool = False
        self.db_version_verified: bool = False

        # use normalized path to make sure username and password don't leak into __repr__
        qualified_path = self._normalize_path(path)
        super().__init__(qualified_path)

    @classmethod
    def _parse_connection_string(cls, connection_string: str) -> urlparse.ParseResult:
        con_params = urlparse.urlparse(connection_string)

        if not con_params.hostname:
            con_params = urlparse.urlparse(f'{cls.SQL_DATABASE_SCHEME}://{connection_string}')

        assert con_params.hostname is not None

        if con_params.scheme != cls.SQL_DATABASE_SCHEME:
            raise ValueError(f'unsupported URL scheme "{con_params.scheme}"')

        return con_params

    @contextlib.contextmanager
    def connect(self) -> Iterator:
        if not self.connected:
            with self.sqla_engine.connect() as connection:
                self.connection = connection
                self.connected = True
                self._verify_db_version()
                yield
            self.connected = False
            self.connection = None
        else:
            yield

    def _verify_db_version(self) -> None:
        if not self.db_version_verified:
            # check for version compatibility
            def version_tuple(version_string: str) -> Sequence[str]:
                return version_string.split('.')

            db_version = self.db_version
            current_version = terracotta.__version__

            if version_tuple(db_version)[:2] != version_tuple(current_version)[:2]:
                raise exceptions.InvalidDatabaseError(
                    f'Version conflict: database was created in v{db_version}, '
                    f'but this is v{current_version}'
                )
            self.db_version_verified = True

    @property  # type: ignore
    @requires_connection
    def db_version(self) -> str:
        """Terracotta version used to create the database"""
        terracotta_table = sqla.Table(
            'terracotta',
            self.sqla_metadata,
            autoload_with=self.sqla_engine
        )
        stmt = sqla.select(terracotta_table.c.version)
        version = self.connection.execute(stmt).scalar()
        return version

    def create(self, keys: Sequence[str], key_descriptions: Mapping[str, str] = None) -> None:
        """Create and initialize database with empty tables.

        This must be called before opening the first connection. The MySQL database must not
        exist already.

        Arguments:

            keys: Key names to use throughout the Terracotta database.
            key_descriptions: Optional (but recommended) full-text description for some keys,
                in the form of ``{key_name: description}``.

        """
        self._create_database()
        self._initialize_database(keys, key_descriptions)

    @abstractmethod
    def _create_database(self) -> None:
        # This might be made abstract, for each subclass to implement specifically
        # Note that some subclasses may not actually create any database here, as
        # it may already exist for some vendors
        pass

    @requires_connection
    def _initialize_database(
        self,
        keys: Sequence[str],
        key_descriptions: Mapping[str, str] = None
    ) -> None:
        if key_descriptions is None:
            key_descriptions = {}
        else:
            key_descriptions = dict(key_descriptions)

        if not all(k in keys for k in key_descriptions.keys()):
            raise exceptions.InvalidKeyError('key description dict contains unknown keys')

        if not all(re.match(r'^\w+$', key) for key in keys):
            raise exceptions.InvalidKeyError('key names must be alphanumeric')

        if any(key in self._RESERVED_KEYS for key in keys):
            raise exceptions.InvalidKeyError(f'key names cannot be one of {self._RESERVED_KEYS!s}')

        terracotta_table = sqla.Table(
            'terracotta', self.sqla_metadata,
            sqla.Column('version', sqla.types.String(255), primary_key=True)
        )
        key_names_table = sqla.Table(
            'key_names', self.sqla_metadata,
            sqla.Column('key_name', sqla.types.String(self.SQL_KEY_SIZE), primary_key=True),
            sqla.Column('description', sqla.types.String(8000))
        )
        _ = sqla.Table(
            'datasets', self.sqla_metadata,
            *[
                sqla.Column(key, sqla.types.String(self.SQL_KEY_SIZE), primary_key=True) for key in keys],  # noqa: E501
            sqla.Column('filepath', sqla.types.String(8000))
        )
        _ = sqla.Table(
            'metadata', self.sqla_metadata,
            *[sqla.Column(key, sqla.types.String(self.SQL_KEY_SIZE), primary_key=True) for key in keys],  # noqa: E501
            *self._METADATA_COLUMNS
        )
        self.sqla_metadata.create_all(self.sqla_engine)

        self.connection.execute(
            terracotta_table.insert().values(version=terracotta.__version__)
        )
        self.connection.execute(
            key_names_table.insert(),
            [dict(key_name=key, description=key_descriptions.get(key, '')) for key in keys]
        )
        self.connection.commit()

        # invalidate key cache  # TODO: Is that actually necessary?
        self._db_keys = None

    @requires_connection
    def get_keys(self) -> OrderedDict:
        keys_table = sqla.Table('key_names', self.sqla_metadata, autoload_with=self.sqla_engine)
        result = self.connection.execute(keys_table.select())
        return OrderedDict(result.all())

    @property
    def key_names(self) -> Tuple[str, ...]:
        """Names of all keys defined by the database"""
        if self._db_keys is None:
            self._db_keys = self.get_keys()
        return tuple(self._db_keys.keys())

    @trace('get_datasets')
    @requires_connection
    def get_datasets(
        self,
        where: Mapping[str, Union[str, List[str]]] = None,
        page: int = 0,
        limit: int = None
    ) -> Dict[Tuple[str, ...], str]:
        # Ensure standardized structure of where items
        if where is None:
            where = {}
        else:
            where = dict(where)
        for key, value in where.items():
            if not isinstance(value, list):
                where[key] = [value]

        datasets_table = sqla.Table('datasets', self.sqla_metadata, autoload_with=self.sqla_engine)
        stmt = (
            datasets_table
            .select()
            .where(
                *[
                    sqla.or_(*[datasets_table.c.get(column) == value for value in values])
                    for column, values in where.items()
                ]
            )
            .order_by(*datasets_table.c.values())
            .limit(limit)
            .offset(page * limit if limit is not None else None)
        )

        result = self.connection.execute(stmt)

        def keytuple(row: Dict[str, Any]) -> Tuple[str, ...]:
            return tuple(row[key] for key in self.key_names)

        datasets = {keytuple(row): row['filepath'] for row in result}
        return datasets

    @trace('get_metadata')
    @requires_connection
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        keys = tuple(self._key_dict_to_sequence(keys))
        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)
        stmt = (
            metadata_table
            .select()
            .where(
                *[
                    metadata_table.c.get(key) == value
                    for key, value in zip(self.key_names, keys)
                ]
            )
        )

        row = self.connection.execute(stmt).first()

        if not row:  # support lazy loading
            filepath = self.get_datasets(dict(zip(self.key_names, keys)))
            if not filepath:
                raise exceptions.DatasetNotFoundError(f'No dataset found for given keys {keys}')
            assert len(filepath) == 1

            # compute metadata and try again
            self.insert(keys, filepath[keys], skip_metadata=False)
            row = self.connection.execute(stmt).first()

        assert row

        data_columns, _ = zip(*self._METADATA_COLUMNS)
        encoded_data = {col: row[col] for col in self.key_names + data_columns}
        return self._decode_data(encoded_data)

    @trace('insert')
    @requires_connection
    def insert(
        self,
        keys: Union[Sequence[str], Mapping[str, str]],
        filepath: str, *,
        metadata: Mapping[str, Any] = None,
        skip_metadata: bool = False,
        override_path: str = None
    ) -> None:
        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        if override_path is None:
            override_path = filepath

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        datasets_table = sqla.Table('datasets', self.sqla_metadata, autoload_with=self.sqla_engine)
        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)

        self.connection.execute(
            datasets_table
            .delete()
            .where(*[datasets_table.c.get(column) == value for column, value in key_dict.items()])
        )
        self.connection.execute(
            datasets_table.insert().values(**key_dict, filepath=override_path)
        )

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(filepath)

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            self.connection.execute(
                metadata_table
                .delete()
                .where(
                    *[metadata_table.c.get(column) == value for column, value in key_dict.items()]
                )
            )
            self.connection.execute(
                metadata_table.insert().values(**key_dict, **encoded_data)
            )

        self.connection.commit()

    @trace('delete')
    @requires_connection
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        datasets_table = sqla.Table('datasets', self.sqla_metadata, autoload_with=self.sqla_engine)
        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)

        self.connection.execute(
            datasets_table
            .delete()
            .where(*[datasets_table.c.get(column) == value for column, value in key_dict.items()])
        )
        self.connection.execute(
            metadata_table
            .delete()
            .where(*[metadata_table.c.get(column) == value for column, value in key_dict.items()])
        )
        self.connection.commit()

    @staticmethod
    def _encode_data(decoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from internal format to database representation"""
        encoded = {
            'bounds_north': decoded['bounds'][0],
            'bounds_east': decoded['bounds'][1],
            'bounds_south': decoded['bounds'][2],
            'bounds_west': decoded['bounds'][3],
            'convex_hull': json.dumps(decoded['convex_hull']),
            'valid_percentage': decoded['valid_percentage'],
            'min': decoded['range'][0],
            'max': decoded['range'][1],
            'mean': decoded['mean'],
            'stdev': decoded['stdev'],
            'percentiles': np.array(decoded['percentiles'], dtype='float32').tobytes(),
            'metadata': json.dumps(decoded['metadata'])
        }
        return encoded

    @staticmethod
    def _decode_data(encoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from database format to internal representation"""
        decoded = {
            'bounds': tuple([encoded[f'bounds_{d}'] for d in ('north', 'east', 'south', 'west')]),
            'convex_hull': json.loads(encoded['convex_hull']),
            'valid_percentage': encoded['valid_percentage'],
            'range': (encoded['min'], encoded['max']),
            'mean': encoded['mean'],
            'stdev': encoded['stdev'],
            'percentiles': np.frombuffer(encoded['percentiles'], dtype='float32').tolist(),
            'metadata': json.loads(encoded['metadata'])
        }
        return decoded
