Available colormaps
===================

.. note::

    Most colormaps also provide a reversed version of themselves with suffix ``_r`` (e.g. ``viridis_r``).


.. raw:: html

    <div class="cmap-gallery-container">

.. exec::

    import os
    from textwrap import dedent
    import numpy as np
    from PIL import Image

    from terracotta.cmaps import AVAILABLE_CMAPS
    from terracotta.image import array_to_png

    img_data = np.asarray(Image.open('_static/example-img.png'))
    cbar_data = np.tile(
        np.arange(0, 256, 1, dtype='uint8'),
        (24, 1)
    )
    outdir = '_generated'

    os.makedirs(outdir, exist_ok=True)

    for cmap in AVAILABLE_CMAPS:
        if cmap.endswith('_r'):
            continue

        imgfile = os.path.join(outdir, f'cmap-{cmap}-img.png')
        with open(imgfile, 'wb') as f:
            f.write(array_to_png(img_data, colormap=cmap).getbuffer())

        cbarfile = os.path.join(outdir, f'cmap-{cmap}-bar.png')
        with open(cbarfile, 'wb') as f:
            f.write(array_to_png(cbar_data, colormap=cmap).getbuffer())

        print(dedent(f'''
            .. raw:: html

                <div class="cmap-gallery">

        '''))

        print(f'**{cmap}**')
        print('')

        print(f'.. image:: /{imgfile}')
        print('')

        print(f'.. image:: /{cbarfile}')
        print('')

        print(dedent(f'''
            .. raw:: html

                </div>

        '''))

.. raw:: html

    </div>
