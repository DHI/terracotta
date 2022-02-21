"""drivers/relational_meta_store.py

Base class for relational database drivers, using SQLAlchemy.
"""

import contextlib
import functools
import json
import re
import urllib.parse as urlparse
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import (Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple,
                    Type, Union)

import numpy as np
import sqlalchemy as sqla
import terracotta
from sqlalchemy.engine.base import Connection
from sqlalchemy.engine.url import URL
from terracotta import exceptions
from terracotta.drivers.base_classes import (KeysType, MetaStore,
                                             MultiValueKeysType,
                                             requires_connection)
from terracotta.profile import trace

_ERROR_ON_CONNECT = (
    'Could not connect to database. Make sure that the given path points '
    'to a valid Terracotta database, and that you ran driver.create().'
)

DATABASE_DRIVER_EXCEPTIONS_TO_CONVERT: Tuple[Type[Exception], ...] = (
    sqla.exc.OperationalError,
    sqla.exc.InternalError,
    sqla.exc.ProgrammingError,
    sqla.exc.InvalidRequestError,
)

ExceptionType = Union[Type[Exception], Tuple[Type[Exception], ...]]


@contextlib.contextmanager
def convert_exceptions(
    error_message: str,
    exceptions_to_convert: ExceptionType = DATABASE_DRIVER_EXCEPTIONS_TO_CONVERT,
) -> Iterator:
    try:
        yield
    except exceptions_to_convert as exception:
        raise exceptions.InvalidDatabaseError(error_message) from exception


class RelationalMetaStore(MetaStore, ABC):
    SQL_DIALECT: str  # The database flavour, eg mysql, sqlite, etc
    SQL_DRIVER: str  # The actual database driver, eg pymysql, sqlite3, etc
    SQL_KEY_SIZE: int
    SQL_TIMEOUT_KEY: str

    SQLA_STRING = sqla.types.String
    SQLA_METADATA_TYPE_LOOKUP: Dict[str, sqla.types.TypeEngine] = {
        'real': functools.partial(sqla.types.Float, precision=8),
        'text': sqla.types.Text,
        'blob': sqla.types.LargeBinary
    }

    _METADATA_COLUMNS: Tuple[Tuple[str, str], ...] = (
        ('bounds_north', 'real'),
        ('bounds_east', 'real'),
        ('bounds_south', 'real'),
        ('bounds_west', 'real'),
        ('convex_hull', 'text'),
        ('valid_percentage', 'real'),
        ('min', 'real'),
        ('max', 'real'),
        ('mean', 'real'),
        ('stdev', 'real'),
        ('percentiles', 'blob'),
        ('metadata', 'text')
    )

    def __init__(self, path: str) -> None:
        settings = terracotta.get_settings()
        db_connection_timeout: int = settings.DB_CONNECTION_TIMEOUT

        self.url = self._parse_path(path)
        self.sqla_engine = sqla.create_engine(
            self.url,
            echo=False,
            future=True,
            connect_args={self.SQL_TIMEOUT_KEY: db_connection_timeout}
        )
        self.sqla_metadata = sqla.MetaData()

        self._db_keys: Optional[OrderedDict] = None

        self.connection: Connection
        self.connected: bool = False
        self.db_version_verified: bool = False

        # use normalized path to make sure username and password don't leak into __repr__
        super().__init__(self._normalize_path(path))

    @classmethod
    def _parse_path(cls, connection_string: str) -> URL:
        if "//" not in connection_string:
            connection_string = f"//{connection_string}"

        con_params = urlparse.urlparse(connection_string)

        if not con_params.scheme:
            con_params = urlparse.urlparse(f'{cls.SQL_DIALECT}:{connection_string}')

        if con_params.scheme != cls.SQL_DIALECT:
            raise ValueError(f'unsupported URL scheme "{con_params.scheme}"')

        url = URL.create(
            drivername=f'{cls.SQL_DIALECT}+{cls.SQL_DRIVER}',
            username=con_params.username,
            password=con_params.password,
            host=con_params.hostname,
            port=con_params.port,
            database=con_params.path[1:],  # remove leading '/' from urlparse
            query=dict(urlparse.parse_qsl(con_params.query))
        )

        return url

    @contextlib.contextmanager
    def connect(self, verify: bool = True) -> Iterator:
        @convert_exceptions(_ERROR_ON_CONNECT, sqla.exc.OperationalError)
        def get_connection() -> Connection:
            return self.sqla_engine.connect().execution_options(isolation_level='READ UNCOMMITTED')

        if not self.connected:
            try:
                with get_connection() as connection:
                    self.connection = connection
                    self.connected = True
                    if verify:
                        self._connection_callback()

                    yield
                    self.connection.commit()
            finally:
                self.connected = False
                self.connection = None
        else:
            try:
                yield
            except Exception as exception:
                self.connection.rollback()
                raise exception

    def _connection_callback(self) -> None:
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
    @convert_exceptions(_ERROR_ON_CONNECT)
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

    @convert_exceptions('Could not create database')
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
        # Note that some subclasses may not actually create any database here, as
        # it may be created automatically on connection for some database vendors
        pass

    @requires_connection(verify=False)
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
            sqla.Column('version', self.SQLA_STRING(255), primary_key=True)
        )
        key_names_table = sqla.Table(
            'key_names', self.sqla_metadata,
            sqla.Column('key_name', self.SQLA_STRING(self.SQL_KEY_SIZE), primary_key=True),
            sqla.Column('description', self.SQLA_STRING(8000)),
            sqla.Column('index', sqla.types.Integer, unique=True)
        )
        _ = sqla.Table(
            'datasets', self.sqla_metadata,
            *[
                sqla.Column(key, self.SQLA_STRING(self.SQL_KEY_SIZE), primary_key=True)
                for key in keys
            ],
            sqla.Column('path', self.SQLA_STRING(8000))
        )
        _ = sqla.Table(
            'metadata', self.sqla_metadata,
            *[
                sqla.Column(key, self.SQLA_STRING(self.SQL_KEY_SIZE), primary_key=True)
                for key in keys],
            *[
                sqla.Column(name, self.SQLA_METADATA_TYPE_LOOKUP[column_type]())
                for name, column_type in self._METADATA_COLUMNS
            ]
        )
        self.sqla_metadata.create_all(self.sqla_engine)

        self.connection.execute(
            terracotta_table.insert().values(version=terracotta.__version__)
        )
        self.connection.execute(
            key_names_table.insert(),
            [
                dict(key_name=key, description=key_descriptions.get(key, ''), index=i)
                for i, key in enumerate(keys)
            ]
        )

    @requires_connection
    @convert_exceptions('Could not retrieve keys from database')
    def get_keys(self) -> OrderedDict:
        keys_table = sqla.Table('key_names', self.sqla_metadata, autoload_with=self.sqla_engine)
        result = self.connection.execute(
            sqla.select(
                keys_table.c.get('key_name'),
                keys_table.c.get('description')
            )
            .order_by(keys_table.c.get('index')))
        return OrderedDict(result.all())

    @property
    def key_names(self) -> Tuple[str, ...]:
        """Names of all keys defined by the database"""
        if self._db_keys is None:
            self._db_keys = self.get_keys()
        return tuple(self._db_keys.keys())

    @trace('get_datasets')
    @requires_connection
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(
        self,
        where: MultiValueKeysType = None,
        page: int = 0,
        limit: int = None
    ) -> Dict[Tuple[str, ...], str]:
        if where is None:
            where = {}

        where = {
            key: value if isinstance(value, list) else [value]
            for key, value in where.items()
        }

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

        datasets = {keytuple(row): row['path'] for row in result}
        return datasets

    @trace('get_metadata')
    @requires_connection
    @convert_exceptions('Could not retrieve metadata')
    def get_metadata(self, keys: KeysType) -> Optional[Dict[str, Any]]:
        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)
        stmt = (
            metadata_table
            .select()
            .where(
                *[
                    metadata_table.c.get(key) == value
                    for key, value in keys.items()
                ]
            )
        )

        row = self.connection.execute(stmt).first()
        if not row:
            return None

        data_columns, _ = zip(*self._METADATA_COLUMNS)
        encoded_data = {col: row[col] for col in self.key_names + data_columns}
        return self._decode_data(encoded_data)

    @trace('insert')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def insert(
        self,
        keys: KeysType,
        path: str, *,
        metadata: Mapping[str, Any] = None
    ) -> None:
        datasets_table = sqla.Table('datasets', self.sqla_metadata, autoload_with=self.sqla_engine)
        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)

        self.connection.execute(
            datasets_table
            .delete()
            .where(*[datasets_table.c.get(column) == value for column, value in keys.items()])
        )
        self.connection.execute(
            datasets_table.insert().values(**keys, path=path)
        )

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            self.connection.execute(
                metadata_table
                .delete()
                .where(
                    *[metadata_table.c.get(column) == value for column, value in keys.items()]
                )
            )
            self.connection.execute(
                metadata_table.insert().values(**keys, **encoded_data)
            )

    @trace('delete')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def delete(self, keys: KeysType) -> None:
        if not self.get_datasets(keys):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        datasets_table = sqla.Table('datasets', self.sqla_metadata, autoload_with=self.sqla_engine)
        metadata_table = sqla.Table('metadata', self.sqla_metadata, autoload_with=self.sqla_engine)

        self.connection.execute(
            datasets_table
            .delete()
            .where(*[datasets_table.c.get(column) == value for column, value in keys.items()])
        )
        self.connection.execute(
            metadata_table
            .delete()
            .where(*[metadata_table.c.get(column) == value for column, value in keys.items()])
        )

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
