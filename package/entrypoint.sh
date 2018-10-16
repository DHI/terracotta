#!/bin/bash

FILENAME="$1"
shift
OTHER_ARGS="$@"

cat - > $FILENAME

source /env/tc-deploy/bin/activate
zappa $OTHER_ARGS -s $FILENAME
