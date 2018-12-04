|Logo|

|Build Status| |Documentation Status| |codecov| |GitHub release|
|License|

Terracotta runs as a WSGI app on a dedicated webserver or as a
serverless app on AWS λ. For convenient data exploration, debugging, and
development, it also runs standalone through the CLI command
``terracotta serve``.

For greatly improved performance, use `Cloud Optimized
GeoTIFFs <http://www.cogeo.org>`__ (COG) with Terracotta. You can
convert all kinds of single-band raster files to COG through the command
``terracotta optimize-rasters``.

Terracotta is built on a modern Python 3.6 stack, powered by awesome
open-source software such as `Flask <http://flask.pocoo.org>`__,
`Zappa <https://github.com/Miserlou/Zappa>`__, and
`Rasterio <https://github.com/mapbox/rasterio>`__.

**Want to know more?**

- `Try the demo <https://terracotta-python.readthedocs.io/en/latest/preview-app.html>`__
- `Read the docs <https://terracotta-python.readthedocs.io/en/latest>`__
- `Explore the API <https://2truhxo59g.execute-api.eu-central-1.amazonaws.com/production/apidoc>`__
- `Satlas, powered by Terracotta <http://satlas.dk>`__


.. |Build Status| image:: https://travis-ci.com/DHI-GRAS/terracotta.svg?token=27HwdYKjJ1yP6smyEa25&branch=master
   :target: https://travis-ci.org/DHI-GRAS/terracotta
.. |Documentation Status| image:: https://readthedocs.org/projects/terracotta-python/badge/?version=latest
   :target: https://terracotta-python.readthedocs.io/en/latest/?badge=latest
.. |codecov| image:: https://codecov.io/gh/DHI-GRAS/terracotta/branch/master/graph/badge.svg?token=u16QBwwvvn
   :target: https://codecov.io/gh/DHI-GRAS/terracotta
.. |GitHub release| image:: https://img.shields.io/github/release/dhi-gras/terracotta.svg
   :target: https://github.com/DHI-GRAS/terracotta/releases
.. |License| image:: https://img.shields.io/github/license/dhi-gras/terracotta.svg
   :target: https://github.com/DHI-GRAS/terracotta/blob/master/LICENSE

.. |Logo| image:: docs/_figures/logo-banner.svg
   :width: 80%
   :target: #
