#!/bin/bash

# Clean up dbus files, then run app.py

if [ $# -lt 1 ] || [ ! -f $1 ]; then
    echo "Usage: $0 [flask app]"
    exit 0
fi
APP=$1

USER=$(whoami)
PID=$(ps -u $USER | grep dbus-daemon | awk '{ print $1 }')

if [ $PID ]; then
    echo "Killing $PID"
    kill $PID
fi

for f in /tmp/omxplayerdbus.$USER /tmp/omxplayerdbus.$USER.pid; do
    if [ -f $f ]; then
	echo "Removing $f"
	rm $f
    fi
done

export FLASK_APP=$APP
export DEBUG=0
flask run --no-reload --host=0.0.0.0
