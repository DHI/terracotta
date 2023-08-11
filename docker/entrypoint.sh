#!/bin/sh

terracotta serve --allow-all-ips --port $TC_SERVER_PORT -d $TC_DRIVER_PATH
