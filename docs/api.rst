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

SQLite driver
-------------

.. autoclass:: terracotta.drivers.sqlite.SQLiteDriver
   :members:
   :undoc-members:
   :special-members: __init__
   :inherited-members:

Remote SQLite driver
--------------------

.. autoclass:: terracotta.drivers.sqlite_remote.RemoteSQLiteDriver
   :members:
   :undoc-members:
   :special-members: __init__
   :inherited-members:
   :exclude-members: delete, insert, create

MySQL driver
------------

.. autoclass:: terracotta.drivers.mysql.MySQLDriver
   :members:
   :undoc-members:
   :special-members: __init__
   :inherited-members:
