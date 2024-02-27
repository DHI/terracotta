#!/bin/sh


# Validate that environment variables are set
if [ -z "$TERRACOTTA_API_URL" ]; then
  echo "TERRACOTTA_API_URL is not set. Exiting."
  exit 1
fi


# Start the server
gunicorn terracotta.client.client_app:client_app --bind 0.0.0.0:$TC_SERVER_PORT
