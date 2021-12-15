Configuration
=============

Most information about the data served by a Terracotta instance is contained in the raster
database. However, there are :ref:`some runtime settings <available-settings>` that apply to the
Terracotta instance as a whole.

Because Terracotta can either run locally, on a web server, or serverless, you can configure these
settings in several different ways:

- Terracotta is fully configurable through environment variables that are prefixed with ``TC_``.
  E.g., running

  .. code-block:: bash

     $ export TC_RESAMPLING_METHOD=cubic

  will set the corresponding setting :attr:`~terracotta.config.TerracottaSettings.RESAMPLING_METHOD` to ``cubic`` in all Terracotta instances. This is particularly useful for serverless deployments. You can set list
  values in JSON array notation:

  .. code-block:: bash

     $ export TC_DEFAULT_TILE_SIZE="[128,128]"

- All :ref:`CLI commands <cli>` accept the path to a TOML file via the ``-c`` flag. Example:

  .. code-block:: bash

     $ terracotta -c config.toml serve -d tc.sqlite

  where ``config.toml`` contains e.g.

  .. code-block:: none

     DRIVER_PATH = root:password@myserver.com/terracotta
     DRIVER_PROVIDER = mysql

- If you are using the :doc:`Terracotta Python API <api>`, you can call
  :func:`~terracotta.update_settings` directly.


.. note::

    If you update a runtime setting while Terracotta is already running, your changes will not take
    effect until :func:`~terracotta.update_settings` is called. In other words, you might have to restart
    your Terracotta server for your changes to take effect.


.. _available-settings:

Available runtime settings
--------------------------

All runtime settings are contained in the following :class:`~typing.NamedTuple`.

.. seealso::

    To see the types and default values of the settings,
    `have a look at the TerracottaSettings source code <_modules/terracotta/config.html#TerracottaSettings>`__.

.. autoclass:: terracotta.config.TerracottaSettings
   :members:
   :member-order: bysource


Cross-origin resource sharing (CORS)
------------------------------------

Your application might need Terracotta to allow CORS for some or all hostnames. For example, this is required when using Mapbox GL to serve tiles (but generally depends on how the frontend requests resources from Terracotta).

You can control the CORS settings for the metadata (``/metadata``) and tiles (``/rgb`` and ``/singleband``)
endpoints individually with the settings :attr:`~terracotta.config.TerracottaSettings.ALLOWED_ORIGINS_METADATA` and :attr:`~terracotta.config.TerracottaSettings.ALLOWED_ORIGINS_TILES`:

.. code-block:: bash

   $ export TC_ALLOWED_ORIGINS_METADATA='["*"]'
   $ export TC_ALLOWED_ORIGINS_TILES="[]"

The above settings are the defaults when you omit these settings (allow all origins for metadata, and no origins for tiles).
