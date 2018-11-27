Get started
===========

.. _installation:

Installation
------------

On most systems, the easiest way to install Terracotta is `through the
Conda package manager <https://conda.io/miniconda.html>`__. After
installing ``conda``, the following command creates a new environment
containing all dependencies and Terracotta:

.. code:: bash

   $ conda env create -f environment.yml

If you already have a Python 3.6 installation that you want to use, you
can just run

.. code:: bash

   $ pip install -e .

in the root of the Terracotta repository instead.

Creating a raster database
--------------------------

For Terracotta to perform well, it is important that some metadata like
the extent of your datasets or the range of its values is computed and
ingested into a database. There are two ways to populate this metadata
store:

1. Through the CLI
++++++++++++++++++

A simple but limited way to build a database is to use the command line
interface. All you need to do is to point Terracotta to a folder of
(cloud-optimized) GeoTiffs:

.. code:: bash

   $ terracotta ingest \
        /path/to/gtiffs/{sensor}_{name}_{date}_{band}.tif \
        -o terracotta.sqlite

This will create a new database with the keys ``sensor``, ``name``,
``date``, and ``band`` (in this order), and ingest all files matching
the given pattern into it.

For available options, see

.. code:: bash

   $ terracotta ingest --help

2. Using the Python API
+++++++++++++++++++++++

Terracotta’s driver API gives you fine-grained control over ingestion
and retrieval. Metadata can be computed at three different times:

1. Automatically during a call to ``driver.insert`` (fine for most
   applications);
2. Manually using ``driver.compute_metadata`` (in case you want to
   decouple computation and IO, or if you want to attach additional
   metadata); or
3. On demand when a dataset is requested for the first time (this is
   what we want to avoid through ingestion).

An example ingestion script using the Python API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following script populates a database with raster files located in a
local directory. It extracts the appropriate keys from the file name,
ingests them into a database, and pushes the rasters and the resulting
database into an S3 bucket.

.. literalinclude:: example-ingestion-script.py
   :language: python
   :caption: example-ingestion-script.py

:download:`Download the script <example-ingestion-script.py>`

Note that the above script is just a simple example to show you some
capabilities of the Terracotta Python API. More sophisticated solutions
could e.g. attach additional metadata to database entries, or accept
parameters from the command line.

Serving data
------------

Connecting to a running Terracotta server
-----------------------------------------