Configuration
=============

Most information about the data served by a Terracotta instance is contained in the raster
database. However, there are :ref:`some runtime settings <available-settings>` that apply to the
Terracotta instance as a whole.

Because Terracotta can either run locally, on a web server, or serverless, you can configure these
settings in several different ways:

- Terracotta is fully configurable through environment variables that are prefixed with ``TC_``.
  E.g., running ``export TC_UPSAMPLING_METHOD=cubic`` will set the corresponding setting 
  ``UPSAMPLING_METHOD`` to ``cubic`` in all Terracotta instances. This is particularly useful
  for serverless deployments. You can set list values in JSON array notation:
  ``export TC_DEFAULT_TILE_SIZE=[128,128]``.

- All :ref:`command line functions <cli>` accept the path to a TOML file via the ``-c`` flag
  (e.g. ``terracotta -c config.toml``).

- If you are using the :ref:`Terracotta Python API <api>`, you can call
  :func:`~terracotta.update_settings` directly.


.. note::

    If you update a runtime setting while Terracotta is already running, your changes will not take
    effect until :func:`~terracotta.update_settings` is called. In other words, you might have to restart
    your Terracotta server for your changes to take effect.


.. _available-settings:

Available runtime settings
--------------------------

.. autoclass:: terracotta.config.TerracottaSettings
   :members: