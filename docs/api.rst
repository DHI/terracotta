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

.. autoclass:: terracotta.drivers.sqlite.SQLiteDriver
   :members: __init__

.. autoclass:: terracotta.drivers.sqlite_remote.RemoteSQLiteDriver
   :members: __init__