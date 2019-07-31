#! /usr/bin/python3

import sys
import os
import shutil
import errno
import random
import string
import subprocess
from jinja2 import Environment, FileSystemLoader
import boto3
from botocore.config import Config
from git import Repo

SITE_NAME = sys.argv[1]
BASE_DIR = os.getcwd()
#TEMPLATE_DIR = os.path.join(BASE_DIR, 'pedigreedb_template/')
DEST_DIR = os.path.join(BASE_DIR, 'instances/{}/{}'.format(SITE_NAME, SITE_NAME))

# Generate passwords
django_password = ''.join([random.choice(string.ascii_letters + string.digits ) for n in range(50)])
db_password = ''.join([random.choice(string.ascii_letters + string.digits ) for n in range(16)])
db_username = 'pedigreedbuser'

boto_config = Config(retries=dict(max_attempts=20))
client = boto3.client(
    'rds', region_name='eu-west-2', config=boto_config
)
db_vars = {
    "DBName": SITE_NAME,
    "DBInstanceIdentifier": SITE_NAME,
    "AllocatedStorage": 20,
    "DBInstanceClass": "db.t2.micro",
    "Engine": "postgres",
    "MasterUsername": db_username,
    "MasterUserPassword": db_password,
    "VpcSecurityGroupIds": [
        "sg-0a2432a6a0c703f5e",
    ],
    "DBSubnetGroupName": "default-vpc-016908fc41dd3e6f8",
    "DBParameterGroupName": "default.postgres10",
    "BackupRetentionPeriod": 7,
    "MultiAZ": False,
    "EngineVersion": "10.6",
    "PubliclyAccessible": True,
    "StorageType": "gp2",
}
new_db = client.create_db_instance(**db_vars)

# clone repo
Repo.clone_from('https://masystems:H5m6RZK0AVh3IumrybH3@github.com/masystems/pedigreedb_template.git', 'instances/{}/{}'.format(SITE_NAME, SITE_NAME))

# copy in dependencies
files = os.listdir('/opt/files/')
for dep in files:
    fullpath = os.path.join('/opt/files/', dep)
    if (os.path.isfile(fullpath)):
        shutil.copy(fullpath, 'instances/{}/{}'.format(SITE_NAME, SITE_NAME))

# set template dir root
env = Environment(loader=FileSystemLoader(DEST_DIR))

# update zappa settings
template = env.get_template('zappa_settings.j2')
with open(os.path.join(DEST_DIR, 'zappa_settings.json'), 'w') as fh:
    fh.write(template.render(site_name=SITE_NAME))


# create virtualenv
subprocess.Popen(['virtualenv', '-p', 'python3', 'instances/{}/venv'.format(SITE_NAME)])

# wait for db to be created
waiter = client.get_waiter("db_instance_available")
waiter.wait(DBInstanceIdentifier=SITE_NAME, WaiterConfig={"Delay": 10, "MaxAttempts": 60},)

# get db endpoint
details = client.describe_db_instances(DBInstanceIdentifier=SITE_NAME)
db_host = details['DBInstances'][0]['Endpoint']['Address']

# update local settings
template = env.get_template('pedigreedb/local_settings.j2')
with open(os.path.join(DEST_DIR, 'pedigreedb/local_settings.py'), 'w') as fh:
    fh.write(template.render(site_name=SITE_NAME,
                             site_mode='hierarchy',
                             django_password=django_password,
                             db_name=SITE_NAME,
                             db_username=db_username,
                             db_password=db_password,
                             db_host=db_host))

subprocess.Popen(['/opt/venv.sh', SITE_NAME, 'instances/{}/'.format(SITE_NAME)])