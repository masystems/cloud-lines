#!/bin/bash

pushd $1

source ../venv/bin/activate

python manage.py makemigrations
python manage.py makemigrations impex
python manage.py migrate --noinput
zappa update

popd