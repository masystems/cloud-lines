#!/bin/bash

pushd $1

source ../venv/bin/activate
pip freeze | xargs pip uninstall -y
pip install -r requirements.txt
python manage.py makemigrations
python manage.py makemigrations impex
python manage.py makemigrations metrics
python manage.py migrate --noinput
zappa update
deactivate
popd