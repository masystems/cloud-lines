#!/bin/bash

pushd $1

source ../venv/bin/activate
if [ "$2" == "pip" ]; then
    pip freeze | xargs pip uninstall -y
fi
pip install -r requirements.txt
python manage.py migrate --noinput
zappa update
deactivate
popd