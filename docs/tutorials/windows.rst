Setting up a Terracotta environment on Windows 10
=================================================

Terracotta comes with full support for Windows 10, even though setup
might be more complicated compared to Unix systems.


Set up conda and install Terracotta
-----------------------------------

1. `Download and install Git for Windows <https://git-scm.com/download/win>`__.

2. `Download and install Miniconda <https://conda.io/miniconda.html>`__.
   If you do not give the installer permissions to append ``conda`` to your PATH,
   you will have to use the Anaconda shell for the following steps.

3. Clone the Terracotta repository to your hard drive by running

   .. code-block:: bash

      $ git clone https://github.com/DHI-GRAS/terracotta.git

   Alternatively, 
   `you can choose and download a release version <https://github.com/DHI-GRAS/terracotta/releases>`__.

4. Go to the Terracotta folder, and run

   .. code-block:: bash

      $ conda env create -f environment.yml

   If the command finished without errors, you have successfully installed
   Terracotta.

5. Before using Terracotta, activate the environment via

   .. code-block:: bash

      $ conda activate terracotta

   You can now use the :doc:`Terracotta CLI <../cli>`:

   .. code-block:: bash

      $ terracotta --help


Optional: Configure AWS credentials
-----------------------------------

Terracotta unfolds its full potential when used with cloud services. All drivers
support raster files located on AWS S3, and databases on S3 (through the
:class:`~terracotta.drivers.sqlite_remote.RemoteSQLiteDriver`) or RDS (through the
:class:`~terracotta.drivers.mysql.MySQLDriver`). To use these features, you need
to create an account and authenticate with it.

1. If you do not have an account on AWS yet, 
   `just head over and create one <https://aws.amazon.com>`__.

2. You will need to create an IAM user that has programmatic access to your account.
   For that purpose, `go to the IAM service <https://console.aws.amazon.com/iam>`__
   and create a new IAM user.

   In the easiest setup, you can give it full permission to your account
   (but make sure to keep the key secret). For that, enter a username (such as
   ``awscli``), check the box ``Programmatic access``, and attach the 
   ``AdministratorAccess`` policy.

3. After you have created the IAM user, AWS will show you the corresponding ID and
   access key. Save those for later.

4. Install the AWS command line tools by executing

   .. code-block:: bash

      $ conda activate terracotta
      $ pip install awscli

   You can now use the AWS CLI:

   .. code-block:: bash

      $ aws --help

5. Configure the credentials to use with the AWS CLI:

   .. code-block:: bash

      $ aws configure

   When asked for it, paste the ID and key of the IAM user you created in step 2.
   You will also have to choose a default AWS region, e.g. ``eu-central-1``.

6. You should now be able to use your AWS account programmatically. You can try this via

   .. code-block:: bash

      $ aws s3 ls

   You should now see a list of your S3 buckets if you have created any.

By configuring the AWS credentials through the AWS CLI, Terracotta is now able to access
all of your resources on AWS.


Optional: Set up Zappa on WSL
-----------------------------

We rely on the magic provided by `Zappa <https://github.com/Miserlou/Zappa>`__ to deploy
Terracotta on AWS Lambda. Since AWS Lambda workers run on Linux, we cannot use a Windows environment
for deployment. This is why we rely on the Windows subsystem for Linux (WSL).

1. First up, `install the Windows subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`__.
   You can install any Linux flavor you want, but in this tutorial we are using Ubuntu.

2. This and all further steps should be executed in a WSL shell. We will have to re-install
   Terracotta and its dependencies inside Linux.

   We will start by installing Python 3.6 and some libraries:

   .. code-block:: bash

      $ sudo add-apt-repository ppa:deadsnakes/ppa
      $ sudo apt update
      $ sudo apt install build-essential gdal-bin git libgdal-dev python3.6-dev

3. Create a new virtual Python environment that we will use to deploy Terracotta:

   .. code-block:: bash

      $ pip install virtualenv --user
      $ virtualenv --python=python3.6 ~/envs/tc-deploy

   Activate the new environment by running

   .. code-block:: bash

      $ source ~/envs/tc-deploy/bin/activate

4. Clone Terracotta inside Linux:

   .. code-block:: bash

      $ git clone https://github.com/DHI-GRAS/terracotta.git
    
5. Switch to the Terracotta folder and install the Zappa requirements and Terracotta:

   .. code-block:: bash

      $ pip install -r zappa_requirements.txt
      $ pip install -e .

6. Install and configure the AWS CLI:

   .. code-block:: bash

      $ pip install awscli
      $ aws configure

And you're done! You should now be able to :doc:`deploy Terracotta on AWS Lambda <aws>`.
