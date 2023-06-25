#!/bin/bash

pushd $1

source ../venv/bin/activate
if [ "$2" == "pip" ]; then
    pip freeze | xargs pip uninstall -y
    pip install -r requirements.txt
fi
python manage.py migrate --noinput
zappa update
deactivate
popd