#!/bin/bash

pushd $1
now=$(date +"%Y%m%d")

source ../venv/bin/activate
mkdir -p ../backups/
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > ../backups/${now}.json
find /var/log -name "*.json" -type f -mtime +30 -exec rm -f {} \;
deactivate
popd