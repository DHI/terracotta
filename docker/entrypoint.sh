#!/bin/sh


# Validate that environment variables are set
if [ -z "$TC_DRIVER_PATH" ]; then
  echo "TC_DRIVER_PATH is not set. Exiting."
  exit 1
fi


# Start the server
gunicorn terracotta.server.app:app --bind 0.0.0.0:$TC_SERVER_PORT
