#!/bin/bash

source ../venv/bin/actviate

python manage.py makemigrations
python manage.py makemigrations impex
python manage.py migrate --noinput
zappa update
