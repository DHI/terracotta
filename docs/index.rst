:tocdepth: 5

Welcome to Terracotta
=====================

Use cases
---------

1. Use it as data exploration tool to quickly serve up a folder
   containing GeoTiff images with ``terracotta serve``.
2. :doc:`Make it your tile server backend on an existing webserver. <tutorials/wsgi>`
   You can ingest your data :ref:`ahead of time <ingestion>` (recommended)
   or on-demand.
3. :doc:`Deploy it on serverless architectures such as AWS Lambda to serve tiles
   from S3 buckets. <tutorials/aws>` This allows you to build apps that
   scale almost infinitely with minimal maintenance!


Installation
------------

If you are using Linux and already have Python 3.6+ installed, all you need to
do to check out Terracotta is

.. code-block:: bash

    $ pip install terracotta[recommended]

Otherwise, see :ref:`our installation guide <installation>` for conda-based
and development installations on all platforms.


Why Terracotta?
---------------

-  It is trivial to get going. Got a folder full of cloud-optimized
   GeoTiffs in different projections you want to have a look at in your
   browser? ``terracotta serve -r {name}.tif`` and
   ``terracotta connect localhost:5000`` get you there.
-  We make minimal assumptions about your data, so *you stay in charge*.
   Keep using the tools you know and love to create and organize your
   data, Terracotta serves it exactly as it is.
-  Serverless deployment is a first-priority use case, so you don’t have
   to worry about maintaining or scaling your architecture.
-  Terracotta instances are self-documenting. Everything the frontend
   needs to know about your data is accessible from only a handful of
   API endpoints.

Web API
-------

Every Terracotta deployment exposes the API it uses as a
``swagger.json`` file and a visual explorer hosted at
``http://server.com/swagger.json`` and ``http://server.com/apidoc``,
respectively. This is the best way to find out which API *your*
deployment of Terracotta uses.

To catch a first glance,
`feel free to explore the API of our demo server <https://2truhxo59g.execute-api.eu-central-1.amazonaws.com/production/apidoc>`__.


Contents
--------

.. toctree::
   :maxdepth: 2

   concepts
   get-started
   settings
   cli
   api
   tutorial
   reference
   issues
