Python API
==========

Get and set runtime settings
----------------------------

.. autofunction:: terracotta.get_settings

.. autofunction:: terracotta.update_settings

Get a driver instance
---------------------

.. autofunction:: terracotta.get_driver

Driver interface
----------------

.. seealso::

   The following class defines the common interface for all Terracotta
   drivers. For a reference on a specific drivers refer to :ref:`available-drivers`.

.. autoclass:: terracotta.drivers.base.Driver
   :members:

.. _available-drivers:

Available drivers
-----------------

.. toctree::
   :maxdepth: 1

   drivers/sqlite
   drivers/sqlite-remote
   drivers/mysql
