Python API
==========

Top-level interface
-------------------

.. autofunction:: terracotta.get_driver

.. autofunction:: terracotta.get_settings

.. autofunction:: terracotta.update_settings

Drivers
-------

Common interface
++++++++++++++++

.. autoclass:: terracotta.drivers.base.Driver
   :members:

Available drivers
+++++++++++++++++

SQLite
~~~~~~

.. autoclass:: terracotta.drivers.sqlite.SQLiteDriver
   :members: __init__

Remote SQLite on S3
~~~~~~~~~~~~~~~~~~~

.. autoclass:: terracotta.drivers.sqlite_remote.RemoteSQLiteDriver
   :members: __init__

MySQL
~~~~~

.. autoclass:: terracotta.drivers.mysql.MySQLDriver
   :members: __init__