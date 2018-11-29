|Build Status| |Documentation Status| |codecov| |GitHub release|
|License|

Terracotta
==========

`Try the demo <https://terracotta-python.readthedocs.io/en/latest/preview-app.html>`__ \|
`Read the docs <https://terracotta-python.readthedocs.io/en/latest>`__ \|
`Explore the API <https://2truhxo59g.execute-api.eu-central-1.amazonaws.com/production/apidoc>`__ \|
`Satlas, powered by Terracotta <http://satlas.dk>`__

A light-weight, versatile XYZ tile server, built with Flask and Rasterio
:earth_africa:

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

Use cases
---------

Terracotta covers three major use cases:

1. Use it as data exploration tool to quickly serve up a folder
   containing GeoTiff images with ``terracotta serve``.
2. Make it your tile server backend on an existing webserver. Refer to
   `the Flask
   documentation <http://flask.pocoo.org/docs/1.0/deploying/>`__ for
   more information. You can ingest your data ahead of
   time (recommended) or on-demand.
3. Deploy it on serverless architectures such as AWS λ to serve tiles
   from S3 buckets. This allows you to build apps that scale almost
   infinitely with minimal maintenance! To make it as easy as possible
   to deploy to AWS λ, we make use of the magic provided by
   `Zappa <https://github.com/Miserlou/Zappa>`__.

Why Terracotta?
---------------

There are many good reasons to ditch your ancient raster data workflow
and switch to Terracotta. Some of them are listed here:

-  It is trivial to get going. Got a folder full of cloud-optimized
   GeoTiffs in different projections you want to have a look at in your
   browser? ``terracotta serve -p {name}.tif`` and
   ``terracotta connect localhost:5000`` get you there.
-  We make minimal assumptions about your data, so *you stay in charge*.
   Keep using the tools you know and love to create and organize your
   data.
-  Serverless deployment is a first-priority use case, so you don’t have
   to worry about maintaining or scaling your architecture.
-  Terracotta instances are self-documenting. Everything the frontend
   needs to know about your data is accessible from only a handful of
   API endpoints.

Data model
----------

Terracotta is agnostic to the organization of your data. You can cast
almost any hierarchy into an API structure through *keys*, which are an
ordered sequence of named categories. Keys can have any names and
(string) values.

For example, surface reflectance for the red, green, and blue spectral
bands at different dates can be represented by the keys
``('type', 'date', 'band')``, where type is ``'reflectance'``, date for
example ``'20181010'``, and bands ``'red'``, ``'green'``, and
``'blue'``.

Every unique combination of the key values is a *dataset*, representing
one single-band image, e.g. ``reflectance/20181010/B04``.

For the example from above, you get a proper RGB representation from a
Terracotta server by querying
``example.com/rgb/reflectance/20181010/{z}/{x}/{y}.png?r=red&g=green&b=blue``.

The number and names of keys are fixed. This is more flexible than it may
sound: In the same scheme as above, you could introduce a type
``'indices'`` and name your band ``'NDVI'`` and get it served on
``example.com/singleband/indices/20181010/NDVI/{z}/{x}/{y}.png``.

Architecture
------------

In Terracotta, all heavy lifting is done by a so-called **driver**. The
driver specifies where and how Terracotta can find the raster data and
metadata it requires to serve a dataset. Most drivers use a database to
store metadata and rely on a file system to store raster data, but
neither of those assumptions are enforced by the API.

Already implemented drivers include:

-  **SQLite + GeoTiff**: Metadata is backed in an SQLite database, along
   with the paths to the (physical) raster files. This is the simplest
   driver, and is used by default in most applications. Both the SQLite
   database and the raster files may be stored in AWS S3 buckets.
-  **MySQL + GeoTiff**: Similar to the SQLite driver, but uses a
   centralized MySQL database to store metadata. This driver is an
   excellent candidate for deployments on cloud services, e.g. through
   `AWS Aurora
   Serverless <https://aws.amazon.com/rds/aurora/serverless/>`__.

Web API
-------

Every Terracotta deployment exposes the API it uses as a
``swagger.json`` file and a visual explorer hosted at
``http://server.com/swagger.json`` and ``http://server.com/apidoc``,
respectively. This is the best way to find out which API *your*
deployment of Terracotta uses.

Limitations
-----------

Terracotta is light-weight and optimized for simplicity and flexibility.
This has a few trade-offs:

-  The number of keys and their names are fixed for one Terracotta
   instance. You have to organize all of your data into the same
   structure - or deploy several instances of Terracotta (see `Data
   model <#data-model>`__ for more information).
-  Terracotta keys are always strings and carry no intrinsic meaning.
   You can search and filter available datasets through exact
   comparisons (e.g. by calling ``/datasets?type=index&date=20180101``),
   but more sophisticated operations have to take place in the frontend.
-  You can only use the last key to compose RGB images (i.e., the last
   key must be ``band`` or similar).
-  Since the names and semantics of the keys of a Terracotta deployment
   are flexible, there are no guarantees that two different Terracotta
   deployments have the same dataset API. However, all information is
   transparently available from the frontend, via the ``/swagger.json``,
   ``/apidoc``, and ``/keys`` API endpoints.
-  While Terracotta is pretty fast, we favor flexibility over raw speed.
   If sub-second response times are a hard requirement for you,
   Terracotta might not be the right tool for the job.


.. |Build Status| image:: https://travis-ci.com/DHI-GRAS/terracotta.svg?token=27HwdYKjJ1yP6smyEa25&branch=master
   :target: https://travis-ci.org/DHI-GRAS/terracotta
.. |Documentation Status| image:: https://readthedocs.org/projects/terracotta-python/badge/?version=latest
   :target: https://terracotta-python.readthedocs.io/en/latest/?badge=latest
.. |codecov| image:: https://codecov.io/gh/DHI-GRAS/terracotta/branch/master/graph/badge.svg?token=u16QBwwvvn
   :target: https://codecov.io/gh/DHI-GRAS/terracotta
.. |GitHub release| image:: https://img.shields.io/github/release/dhi-gras/terracotta.svg
.. |License| image:: https://img.shields.io/github/license/dhi-gras/terracotta.svg

