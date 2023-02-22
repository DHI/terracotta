A serverless Terracotta deployment on AWS Lambda
================================================

.. warning::

   While it is possible to use Terracotta entirely within AWS' free tier,
   using AWS to deploy Terracotta will probably incur some charges to your
   account. Make sure to check the pricing policy of all relevant services
   for your specific region.

Environment setup
-----------------

The easiest way to deploy Terracotta to AWS Lambda is by using
`Zappa <https://github.com/Miserlou/Zappa>`__. Zappa takes care of packaging
Terracotta and its dependencies, and creates endpoints on AWS Lambda and API
Gateway for us.

.. seealso::

   Zappa works best on Linux. Windows 10 users can use the
   :doc:`Windows Subsystem for Linux <windows>` to deploy Terracotta.

Assuming you alredy have Terracotta installed, follow these steps to setup
a deployment environment:

1. Create and activate a new virtual environment (here called ``tc-deploy``),
   e.g. via

   .. code-block:: bash

      $ pip install virtualenv --user
      $ virtualenv ~/envs/tc-deploy --python=python3.6
      $ source ~/envs/tc-deploy/bin/activate

   If you do not have Python 3.6 installed, one way to get it is via the
   ``deadsnakes`` PPA (on Ubuntu):

   .. code-block:: bash

      $ sudo add-apt-repository ppa:deadsnakes/ppa
      $ sudo apt update
      $ sudo apt install python3.6-dev

   Alternatively, you can use ``pyenv`` or ``conda``.

2. Install all relevant dependencies and Terracotta via

   .. code-block:: bash

      $ pip install -r zappa_requirements.txt
      $ pip install -e .

   in the root of the Terracotta repository.

3. Install the AWS command line tools via

   .. code-block:: bash

      $ pip install awscli

4. Configure access to AWS by running

   .. code-block:: bash

      $ aws configure

   This requires that you have an account `on AWS <aws.amazon.com>`__ and a valid
   IAM user with programmatic access to all relevant resources.

Make sure that you have proper access to S3 and AWS Lambda before continuing, e.g. by
running

.. code-block:: bash

   $ aws s3 ls


Optional: Setup a MySQL server on RDS
-------------------------------------

Setting up a dedicated MySQL server for your Terracotta database is slightly
more cumbersome than relying on SQLite, but has some decisive advantages:

- Removes the overhead of downloading the SQLite database.
- The contents of the database are accessible from the outside, and ingesting
  additional data is more straightforward.
- Multiple Terracotta instances can use the same database server.

To set up a MySQL server on AWS, just follow these steps:

1. `Head over to RDS <https://console.aws.amazon.com/rds>`__ and create a new
   MySQL instance. You can either use one of the free-tier, dedicated MySQL
   servers, or the AWS Aurora MySQL flavor.

   The default settings for RDS are unfortunately far from optimal for
   Terracotta. You should tweak them by creating a new "parameter group"
   and setting

   ::

      wait_timeout = 1
      max_connections = 16000

   Don't forget to apply the parameter group to your RDS instance.

2. By default, your Terracotta Lambda function will not have access to the
   RDS instance. To allow access, you will have to add it to the same security
   group and subnets as your RDS instance. You can achieve this by adding a
   section like this one to your ``zappa_settings.toml`` (see below):

   ::

      [development.vpc_config]
      SubnetIds = ["subnet-xxxxxxxx","subnet-yyyyyyyy", "subnet-zzzzzzzz"]
      SecurityGroupIds = ["sg-xxxxxxxxxxxxxxxxx"]

   You can extract the correct IDs by clicking on your RDS instance.

3. By adding the Lambda function to a VPC, it loses access to S3. To re-enable
   it, `go to the VPC settings <https://console.aws.amazon.com/vpc>`__ and
   create an endpoint for the VPC of the Lambda function, pointing to AWS S3
   (e.g. ``com.amazonaws.eu-central-1.s3``).

You are now ready to continue with the following step!


Populate data storage and database
----------------------------------

The recommended way to ingest your optimized raster files into the database
is through :doc:`the Terracotta Python API <../api>`. To initialize your
database, just run something like

.. code-block:: python

   >>> import terracotta as tc

   >>> # for sqlite
   >>> driver = tc.get_driver('tc.sqlite')

   >>> # for mysql
   >>> driver = tc.get_driver('mysql://user:password@hostname/database')

   >>> key_names = ('type', 'date', 'band')
   >>> driver.create(key_names)

You can then ingest your raster files into the database:

.. code-block:: python

   >>> rasters = {
   ...     ('index', '20180101', 'ndvi'): 'S2_20180101_NDVI.tif',
   ...     ('reflectance', '20180101', 'B04'): 'S2_20180101_B04.tif',
   ... }
   >>> for keys, raster_file in rasters.items():
   ...     driver.insert(keys, raster_file,
   ...                   override_path=f's3://tc-data/rasters/{raster_file}')

Verify that everything went well by executing

.. code-block:: python

   >>> driver.get_datasets()
   {
       ('index', '20180101', 'ndvi'): 's3://tc-data/rasters/S2_20180101_NDVI.tif',
       ('reflectance', '20180101', 'B04'): 's3://tc-data/rasters/S2_20180101_B04.tif',
   }

Finally, just make sure that your raster files end up in the place where
Terracotta is looking for them (the paths returned by
:meth:`~terracotta.drivers.sqlite.SQLiteDriver.get_datasets`). You can e.g.
use the AWS CLI:

.. code-block:: bash

   $ aws s3 sync /path/to/rasters s3://tc-data/rasters
   $ aws s3 cp /path/to/tc.sqlite s3://tc-data/tc.sqlite # if using sqlite

To verify whether everything went well, you can start a local Terracotta
server:

.. code-block:: bash

   $ terracotta serve s3://tc-data/tc.sqlite
   $ terracotta connect localhost:5000


Deploy via Zappa
----------------

The Terracotta repository contains a template with sensible default values for
most Zappa settings:

.. literalinclude:: ../../zappa_settings.toml.in
   :caption: zappa_settings.toml.in

Copy or rename ``zappa_settings.toml.in`` to ``zappa_settings.toml`` and insert
the correct path to your Terracotta database into the environment variables.
To execute the deployment, run

.. code-block:: bash

   $ source ~/envs/tc-deploy/bin/activate
   $ zappa deploy development

Congratulations, your Terracotta instance should now be reachable! You can
verify the deployment via :doc:`terracotta connect <../cli-commands/connect>`.
