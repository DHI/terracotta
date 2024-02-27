#!/bin/sh

DEFAULT_TERRACOTTA_SERVICE="tiler"
API_SERVICE_KEYWORD="tiler"
CLIENT_SERVICE_KEYWORD="client"


# Validate that environment variables are set
if [ -z "$TERRACOTTA_SERVICE" ]; then
  echo "TERRACOTTA_SERVICE is not set. Using default value: $DEFAULT_TERRACOTTA_SERVICE"
  TERRACOTTA_SERVICE=$DEFAULT_TERRACOTTA_SERVICE
fi


if [ $TERRACOTTA_SERVICE = $API_SERVICE_KEYWORD ]; then
   ./entrypoint_api.sh
elif [ $TERRACOTTA_SERVICE = $CLIENT_SERVICE_KEYWORD ]; then
   ./entrypoint_client.sh
else
  echo "TERRACOTTA_SERVICE is not set to a valid value. Exiting."
  exit 1
fi
