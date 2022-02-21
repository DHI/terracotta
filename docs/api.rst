Python API
==========

Get and set runtime settings
----------------------------

.. autofunction:: terracotta.get_settings

.. autofunction:: terracotta.update_settings

.. _drivers:

Get a driver instance
---------------------

.. autofunction:: terracotta.get_driver

TerracottaDriver
----------------

.. autoclass:: terracotta.drivers.TerracottaDriver
   :members:


Supported metadata stores
-------------------------

SQLite metadata store
+++++++++++++++++++++

.. autoclass:: terracotta.drivers.sqlite_meta_store.SQLiteMetaStore

Remote SQLite metadata store
++++++++++++++++++++++++++++

.. autoclass:: terracotta.drivers.sqlite_remote_meta_store.RemoteSQLiteMetaStore

MySQL metadata store
++++++++++++++++++++

.. autoclass:: terracotta.drivers.mysql_meta_store.MySQLMetaStore
