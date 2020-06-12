How to register custom colormaps
================================

Terracotta has a number of :doc:`built-in colormaps </reference/colormaps>`, but if you find something missing, it is possible to supply your own.

Colormaps are shipped in ``.npy`` binary format and consist of a single array with shape ``(255, 4)``, 255 values and four (RGBA) channels, and dtype ``uint8``. So you can e.g. create your own colormap files like this::

   >>> import numpy as np
   >>> cmap_data = np.stack((
   ...     np.arange(0, 255, dtype='uint8'),
   ...     np.arange(0, 255, dtype='uint8'),
   ...     np.arange(0, 255, dtype='uint8'),
   ...     np.full(255, 255, dtype='uint8')
   ... ), axis=1)
   >>> np.save('mycmap_rgba.npy', cmap_data)

This creates a simple greyscale colormap (linearly increasing from 0 to 255 in all RGB channels, and constant alpha channel) and saves it as ``mycmap_rgba.npy``.

.. note::

   For Terracotta to recognize your custom colormaps, their filenames have to end with ``_rgba.npy``.

To register your custom colormaps, you need to set the environment variable ``TC_EXTRA_CMAP_FOLDER`` before starting / importing Terracotta:

.. code:: bash

   $ export TC_EXTRA_CMAP_FOLDER=$HOME/tc-cmaps
   $ terracotta serve -d tc.sqlite

Terracotta will automatically discover your colormaps in the given folder (if they are in the correct format) and serve them in the same way as our built-in colormaps.
