A traditional Terracotta deployment with Nginx and Gunicorn
===========================================================

This tutorial describes how to deploy Terracotta on a server running Ubunutu
18.04. For this we will use Gunicorn to spin up the WSGI instance and
Nginx to proxy incoming requests. Systemd will take care of keeping the
Gunicron running. To serve Terracotta from a Ubuntu VM we will need the
following:

-  A server with Ubuntu 18.04 installed and a non-root user with sudo
   privileges
-  Install Anaconda, Terracotta, Nginx and Gunicorn
-  Some data to display

The username of the VM is assumed to be ``ubuntu``. The IP of the VM
will be used as the domain name (``VM_IP``).


Installation
------------

First we need a Ubuntu 18.04 VM (e.g. on Microsoft Azure) and install
Anaconda on it. After installing Anaconda we can create a new conda
environment and install Terracotta and Gunicorn:

.. code-block:: bash

   $ conda create --name gunicorn
   $ source activate ENVNAME
   $ sudo apt install build-essential gdal-bin libgdal-dev
   $ pip install cython
   $ cd /path/to/terracotta
   $ pip install -e .
   $ pip install gunicorn

Additionally we will need to install Nginx:

.. code-block:: bash

   $ sudo apt install nginx

Check if everything is running fine with:

.. code-block:: bash

   $ sudo systemctl status nginx

If the status check went fine and the firewall is configured correctly,
you should now be able to access the default nginx page via:

::

   http://your_server_ip

For further instructions on how to initially set up Nginx check
`here <https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04>`__.


Get data and optimize for Terracotta
------------------------------------

Copy the rasters you want to serve to ``/mnt/data``, optimize them with
``terracotta optimize-rasters`` and create a database with
``terracotta ingest``:

.. code-block:: bash

   $ terracotta optimize-rasters /mnt/data/rasters/*.tif -o /mnt/data/optimized-rasters
   $ terracotta ingest /mnt/data/optimized-rasters/{name}.tif -o /mnt/data/terracotta.sqlite

This will create the database at ``/mnt/data/terracotta.sqlite`` which we
will need later. While this is running we can set up systemd and nginx


Systemd
-------

Systemd will take care of starting and restarting the Gunicorn process.
For that we create a file ``/etc/systemd/system/terracotta.service``:

.. code-block:: ini

   [Unit]
   Description=Gunicorn instance to serve Terracotta
   After=network.target

   [Service]
   User=sammy
   Group=www-data
   WorkingDirectory=/mnt/data
   Environment="PATH=/home/ubuntu/anaconda3/envs/gunicorn/bin"
   Environment="TC_DRIVER_PATH=/mnt/data/terracotta.sqlite"
   ExecStart=/home/ubuntu/anaconda3/envs/gunicorn/bin/gunicorn \
                --workers 3 --bind unix:terracotta.sock -m 007 terracotta.server.app:app

   [Install]
   WantedBy=multi-user.target

All necessary environment variables like ``TC_DRIVER_PATH`` can be set
by adding multiple ``Environment`` lines. ``ExecStart`` contains the
Gunicorn command that starts the Terracotta instance. It consists of:

-  Absolute path to Gunicorn executable
-  Number of workers to spawn (2 \* cores + 1 is recommended)
-  Binding to a unix socket file ``terracotta.sock`` in the working
   directory
-  Dotted path to the WSGI entry point, which consists of the path to
   the python module containing the main Flask app and the app object:
   ``terracotta.server.app:app``

The service and be started/enabled/restarted with:

.. code-block:: bash

   $ sudo systemctl start terracotta
   $ sudo systemctl enable terracotta
   $ sudo systemctl restart terracotta


Nginx
-----

The Gunicorn server is now running and the we can configure Nginx to
forward requests to it. Create a file
``/etc/ngix/sites-available/terrcotta`` with the contents:

::

   server {
       listen 80;
       server_name VM_IP;

       location / {
           include proxy_params;
           proxy_pass http://unix:/mnt/data/terracotta.sock;
       }
   }

And link it to the sites-enabled folder and restart nginx and terracotta
services.

.. code-block:: bash

   $ sudo ln -s /etc/nginx/sites-available/terracotta /etc/nginx/sites-enabled/terracotta
   $ sudo systemctl restart nginx
   $ sudo systemctl restart terracotta

To check errors in the service and nginx files:

.. code-block:: bash

   $ sudo nginx -t

This guide is adjusted from `here <https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04>`__.


Optional: SSL Encryption
------------------------

One way to encrypt the traffic from and to Terracotta is to generate a
self-signed certificate. This process is described in depth
`here <https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-18-04#step-2-%E2%80%93-configuring-nginx-to-use-ssl>`__.
In this recipe only the main commands are quoted.

To create a self signed key/certificate pair run

.. code-block:: bash

   $ sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt

and enter the requested information. We also create a Diffie-Hellman
group with:

.. code-block:: bash

   $ sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096

This takes several minutes.

Now we need two additional Nginx config files. The first one tells Nginx
where the key/certificate pair can be found and is placed at
``/etc/nginx/snippets/self-signed.conf``:

::

   ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
   ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

The second one (``/etc/nginx/snippets/ssl-params.conf``) contains some
SSL encryption settings:

::

   ssl_protocols TLSv1.2;
   ssl_prefer_server_ciphers on;
   ssl_dhparam /etc/nginx/dhparam.pem;
   ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
   ssl_ecdh_curve secp384r1; # Requires nginx >= 1.1.0
   ssl_session_timeout  10m;
   ssl_session_cache shared:SSL:10m;
   ssl_session_tickets off; # Requires nginx >= 1.5.9
   ssl_stapling on; # Requires nginx >= 1.3.7
   ssl_stapling_verify on; # Requires nginx => 1.3.7
   resolver 8.8.8.8 8.8.4.4 valid=300s;
   resolver_timeout 5s;
   # Disable strict transport security for now. You can uncomment the following
   # line if you understand the implications.
   # add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
   add_header X-Frame-Options DENY;
   add_header X-Content-Type-Options nosniff;
   add_header X-XSS-Protection "1; mode=block";

With these in place we can update the Nginx config file. It essentially
just performs a redirect from port 80 to 443. The new config file
``/etc/nginx/sites-available/terracotta`` should look similar to this:

::

   server {
       listen 443 ssl;
       listen [::]:443 ssl;
       include snippets/self-signed.conf;
       include snippets/ssl-params.conf;

       server_name VM_IP;

       location / {
           include proxy_params;
           proxy_pass http://unix:/mnt/data/terracotta.sock
       }
   }

   server {
       listen 80;
       listen [::]:80;

       server_name VM_IP;

       return 301 https://$server_name$request_uri;
   }

Finally check the syntax and restart Nginx.

.. code-block:: bash

   $ sudo nginx -t
   $ sudo systemctl restart nginx

The warning of the syntax check as well as when you access the server
for the first time via ``https://VM_IP`` are expected because we are
using a self signed SSL certificate. The traffic is encrypted, the
certificate is just not signed by any of the trusted certificate
authorities.
