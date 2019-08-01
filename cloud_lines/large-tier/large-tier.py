import django
import sys
import os
import shutil
import random
import string
import subprocess
from jinja2 import Environment, FileSystemLoader
import boto3
from botocore.config import Config
from git import Repo
import json

sys.path.append('/opt/cloudlines/cloud-lines')
os.environ["DJANGO_SETTINGS_MODULE"] = "cloudlines.settings"
django.setup()

from cloud_lines.models import LargeTierQueue


class LargeTier:
    def __init__(self):

        self.waiting = LargeTierQueue.objects.filter(build_state='waiting')

        # Generate passwords
        self.django_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(50)])
        self.db_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])
        self.db_username = 'pedigreedbuser'

        self.boto_config = Config(retries=dict(max_attempts=20))

        self.dependency_packages = os.listdir('/opt/dependencies/')


    def deploy(self):
        for deployment in self.waiting:
            self.site_name = deployment.subdomain
            self.target_dir = '/opt/instances/{}/{}'.format(self.site_name, self.site_name)

            # set template dir root
            self.env = Environment(loader=FileSystemLoader(self.target_dir))

            self.site_name = deployment.subdomain
            # create database
            client = boto3.client(
                'rds', region_name='eu-west-2', config=self.boto_config
            )
            db_vars = {
                "DBName": self.site_name,
                "DBInstanceIdentifier": self.site_name,
                "AllocatedStorage": 20,
                "DBInstanceClass": "db.t2.micro",
                "Engine": "postgres",
                "MasterUsername": self.db_username,
                "MasterUserPassword": self.db_password,
                "VpcSecurityGroupIds": [
                    "sg-0a2432a6a0c703f5e",
                ],
                "DBSubnetGroupName": "default-vpc-016908fc41dd3e6f8",
                "DBParameterGroupName": "default.postgres10",
                "BackupRetentionPeriod": 0,
                "MultiAZ": False,
                "EngineVersion": "10.6",
                "PubliclyAccessible": True,
                "StorageType": "gp2",
            }
            new_db = client.create_db_instance(**db_vars)

            # clone repo
            print('clone repo')
            Repo.clone_from('https://masystems:H5m6RZK0AVh3IumrybH3@github.com/masystems/cloud-lines.git',
                            self.target_dir)

            # copy in dependencies
            print('copy dependcies')
            for dep in self.dependency_packages:
                fullpath = os.path.join('/opt/dependcies/', dep)
                if os.path.isfile(fullpath):
                    shutil.copy(fullpath, self.target_dir)

            # update zappa settings
            print('set zappa settings')
            template = self.env.get_template('zappa_settings.j2')
            with open(os.path.join(self.target_dir, 'zappa_settings.json'), 'w') as fh:
                fh.write(template.render(site_name=self.site_name))

            # create virtualenv
            print('creating virtual env')
            subprocess.Popen(['virtualenv', '-p', 'python3', '/opt/instances/{}/venv'.format(self.site_name)])

            # wait for db to be created
            print('wating for DB to be created')
            waiter = client.get_waiter("db_instance_available")
            waiter.wait(DBInstanceIdentifier=self.site_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60}, )

            # get db endpoint
            print('getting db endpoint')
            details = client.describe_db_instances(DBInstanceIdentifier=self.site_name)
            db_host = details['DBInstances'][0]['Endpoint']['Address']

            # update local settings
            template = self.env.get_template('cloudlines/local_settings.j2')
            with open(os.path.join(self.target_dir, 'cloudlines/local_settings.py'), 'w') as fh:
                fh.write(template.render(site_name=self.site_name,
                                         site_mode='hierarchy',
                                         django_password=self.django_password,
                                         db_name=self.site_name,
                                         db_username=self.db_username,
                                         db_password=self.db_password,
                                         db_host=db_host))

            # generate user data
            process = subprocess.Popen(['python3', 'manage.py', 'dumpdata', 'auth.user'], stdout=subprocess.PIPE)
            stdout = process.communicate()[0]

            users = json.loads(stdout)
            for user in users:
                if user['pk'] == deployment.user.pk:
                    with open(os.path.join(self.target_dir, 'user.json'), 'w') as outfile:
                        json.dump(user, outfile)

            # run commands inside the venv
            subprocess.Popen(['/opt/venv.sh',
                              self.site_name, # $SITE_NAME
                              deployment.pk, # $USER_PK
                              deployment.attached_service.service.pk, # $SERVICE_PK
                              deployment.user_detail.stripe_id, # $STRIPE_ID
                              deployment.attached_service.site_mode, # $SITE_MODE
                              deployment.attached_service.animal_type,  # $ANIMAL_TYPE
            ])


if __name__ == '__main__':
    lt = LargeTier()
    lt.deploy()
