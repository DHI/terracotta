A serverless Terracotta deployment on AWS
=========================================

The easiest way to deploy Terracotta to AWS λ is by using
`Zappa <https://github.com/Miserlou/Zappa>`__. This repository contains
a template with sensible default values for most Zappa settings.

.. note::
    Note that Zappa works best on Linux. Windows 10 users can use the
    `Windows Subsystem for
    Linux <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`__ to
    deploy Terracotta.

Environment setup
-----------------

Create and activate a new virtual environment (here called ``tc-deploy``).
Install all relevant dependencies via ``pip install -r zappa_requirements.txt``.
Install the AWS command line tools via ``pip install awscli``.
Configure access to AWS by running ``aws configure``. Make sure that you have proper access to S3 and AWS λ before continuing.

Optional: Setup MySQL server on RDS
-----------------------------------

Populate data storage and create database
-----------------------------------------

If you haven’t already done so, create the Terracotta database you
   want to use, and upload your raster files to S3.

Deploy via Zappa
----------------

Copy or rename ``zappa_settings.toml.in`` to ``zappa_settings.toml`` and insert the correct path to your Terracotta database.
Run ``zappa deploy development`` or ``zappa deploy production``. Congratulations, your Terracotta instance should now be reachable!

Verify deployment
-----------------
