#!/bin/bash

pushd $1
now=$(date +"%Y%m%d")

source ../venv/bin/activate
mkdir -p ../backups/
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > ../backups/${now}.json
deactivate
popdll