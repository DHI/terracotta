Get started
===========

.. _installation:

Installation
------------

On most systems, the easiest way to install Terracotta is `through the
Conda package manager <https://conda.io/miniconda.html>`__. Just
install ``conda``, clone the repository, and execute the following command
to create a new environment containing all dependencies and Terracotta:

.. code-block:: bash

   $ conda env create -f environment.yml

If you already have a Python 3.6 installation that you want to use, you
can just run

.. code-block:: bash

   $ pip install -e .

in the root of the Terracotta repository instead.

.. seealso::

   If you are using Windows 10 and find yourself struggling with installing
   Terracotta, :doc:`check out our Windows 10 installation guide <tutorials/windows>`!


Usage in a nutshell
-------------------

The simplest way to use Terracotta is to cycle through the following commands:

1. :doc:`terracotta optimize-rasters <cli-commands/optimize-rasters>` to
   pre-process your raster files;
2. :doc:`terracotta ingest <cli-commands/ingest>` to create a database;
3. :doc:`terracotta serve <cli-commands/serve>` to spawn a server; and
4. :doc:`terracotta connect <cli-commands/connect>` to connect to this server.

The following sections guide you through these steps in more detail.


Data exploration through Terracotta
-----------------------------------

If you have some raster files lying around (e.g. in GeoTiff format),
you can use Terracotta to serve them up.

.. note::

   Terracotta benefits greatly from the
   `cloud-optimized GeoTiff format <https://www.cogeo.org/>`__.
   If your raster files are not cloud-optimized or you are unsure,
   you can preprocess them with
   :doc:`terracotta optimize-rasters <cli-commands/optimize-rasters>`.

Assume you are in a folder containing some files named with the pattern
:file:`S2A_<date>_<band>.tif`. You can start a Terracotta server via

.. code-block:: bash

   $ terracotta serve -r {}_{date}_{band}.tif

which will serve your data at ``http://localhost:5000``. Try the following
URLs and see what happens:

- `localhost:5000/keys <http://localhost:5000/keys>`__
- `localhost:5000/datasets <http://localhost:5000/datasets>`__
- `localhost:5000/apidoc <http://localhost:5000/apidoc>`__

Because it is cumbersome to explore a Terracotta instance by manually
constructing URLs, we have built a tool that lets you inspect it
interactively:

.. code-block:: bash

   $ terracotta connect localhost:5000

If you did everything correctly, a new window should open in your browser that lets you explore the dataset.

.. _ingestion:

Creating a raster database
--------------------------

For Terracotta to perform well, it is important that some metadata like
the extent of your datasets or the range of its values is computed and
ingested into a database. There are two ways to populate this metadata
store:

1. Through the CLI
++++++++++++++++++

A simple but limited way to build a database is to use
:doc:`terracotta ingest <cli-commands/ingest>`. All you need to do is
to point Terracotta to a folder of (cloud-optimized) GeoTiffs:

.. code-block:: bash

   $ terracotta ingest \
        /path/to/gtiffs/{sensor}_{name}_{date}_{band}.tif \
        -o terracotta.sqlite

This will create a new database with the keys ``sensor``, ``name``,
``date``, and ``band`` (in this order), and ingest all files matching
the given pattern into it.

For available options, see

.. code-block:: bash

   $ terracotta ingest --help

**Note:** The CLI ``ingest`` command relies on naming conventions
to match files against the specified key patterns. The value that matches
is restricted to alphanumerics (i.e. letters and numbers). Other characters
(e.g. the ``_`` in the example above, but also ``-``, ``+``, etc) are considered
separators between keys. So if your filename looks like ``sar_2019-06-24.tif``
then ``{sensor}_{date}.tif`` will not match.

Alternatives include renaming the files (e.g. to ``sar_20190624.tif``), using
an alternative pattern (e.g. ``{sensor}_{year}-{month}-{day}.tif``) or using
the Python API instead of the CLI to perform the ingest.

2. Using the Python API
+++++++++++++++++++++++

:ref:`Terracotta’s driver API <drivers>` gives you fine-grained control
over ingestion and retrieval. Metadata can be computed at three
different times:

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

.. literalinclude:: _static/example-ingestion-script.py
   :language: python
   :caption: example-ingestion-script.py

:download:`Download the script <_static/example-ingestion-script.py>`

.. note::

   The above script is just a simple example to show you some
   capabilities of the Terracotta Python API. More sophisticated solutions
   could e.g. attach additional metadata to database entries, process
   many rasters in parallel, or accept parameters from the command line.


Serving data from a raster database
-----------------------------------

After creating a database, you can use
:doc:`terracotta serve <cli-commands/serve>` to serve the rasters
inserted into it:

.. code-block:: bash

   $ terracotta serve -d /path/to/database.sqlite

To explore the server, you can once again use
:doc:`terracotta connect <cli-commands/connect>`:

.. code-block:: bash

   $ terracotta connect localhost:5000

However, the server spawned by ``terracotta serve`` is indended for
development and data exploration only. For sophisticated production
deployments, :doc:`have a look at our tutorials <tutorial>`.

If you are unsure which kind of deployment to choose, we recommend
you to try out a :doc:`serverless deployment on AWS Lambda <tutorials/aws>`,
via the remote SQLite driver.
