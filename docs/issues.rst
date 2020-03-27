Known issues
============

The sections below outline some common issues people encounter when
using Terracotta. If your problem persists, `feel free to open an
issue <https://github.com/DHI-GRAS/terracotta/issues>`__.

``OSError: error while reading file`` while deploying to AWS Lambda
-------------------------------------------------------------------

Rasterio Linux wheels are built on CentOS, which stores SSL certificates
in ``/etc/pki/tls/certs/ca-bundle.crt``. On other Linux flavors,
certificates may be stored in a different location. On Ubuntu, you can
e.g. run

.. code-block:: bash

   $ export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

to fix this issue. For more information, see
`mapbox/rasterio#942 <https://github.com/mapbox/rasterio/issues/942>`__.
