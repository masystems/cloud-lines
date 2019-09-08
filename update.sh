#!/bin/bash

pushd $1

source ../venv/bin/activate
pip install - r requirements.txt
python manage.py makemigrations
python manage.py makemigrations impex
python manage.py migrate --noinput
zappa update

popd