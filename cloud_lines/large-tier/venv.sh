#! /bin/bash

# change dir
pushd ${BASH_ARGV[0]}

# enter venv
source venv/bin/activate

cd ${BASH_ARGV[1]}

pip install -r requirements.txt

# zappa commands
echo "INIT"
zappa init
sleep 5
while true; do
    echo "DEPLOY"
    if zappa deploy ${BASH_ARGV[1]} | grep -q 'Error: Warning!'; then
        continue
    else
        break
    fi
done
echo "CERTIFY"
zappa certify --yes
sleep 5
echo "COLLECTSTATIC"
zappa manage ${BASH_ARGV[1]} "collectstatic --noinput"
sleep 5
zappa update ${BASH_ARGV[1]}
sleep 5
zappa manage ${BASH_ARGV[1]} migrate
sleep 5
echo "MAKEMIGRATIONS"
python manage.py makemigrations
echo "MIGRATE"
python manage.py migrate
echo "UPDATE"
zappa update ${BASH_ARGV[1]}
echo "USER: MARCO"
zappa invoke --raw ${BASH_ARGV[1]} "from django.contrib.auth.models import User; User.objects.create_superuser('marco', 'marco@masys.co.uk', '')"
echo "USER: ADAM"
zappa invoke --raw ${BASH_ARGV[1]} "from django.contrib.auth.models import User; User.objects.create_superuser('adam', 'adam@masys.co.uk', '')"
zappa invoke --raw ${BASH_ARGV[1]} "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='editors')"

deactivate

popd