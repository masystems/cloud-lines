#!/usr/bin/python3
import django
import sys
import os
import shutil
import random
import string
import subprocess
import requests
from jinja2 import Environment, FileSystemLoader
import boto3
from botocore.config import Config
from git import Repo
import json

sys.path.append('/opt/cloudlines/cloud-lines')
os.environ["DJANGO_SETTINGS_MODULE"] = "cloudlines.settings"
django.setup()

from cloud_lines.models import LargeTierQueue
from account.views import send_mail

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
            # update settings
            deployment.build_state = 'building'
            deployment.save()

            self.site_name = deployment.subdomain
            self.target_dir = '/opt/instances/{}/{}'.format(self.site_name, self.site_name)

            # set template dir root
            self.env = Environment(loader=FileSystemLoader(self.target_dir))

            self.site_name = deployment.subdomain

            # update settings
            deployment.build_status = "Captured your settings"
            deployment.save()

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

            # update settings
            deployment.build_status = deployment.build_status + "\nInitiating database creation"
            deployment.save()

            # clone repo
            print('clone repo')
            Repo.clone_from('https://masystems:H5m6RZK0AVh3IumrybH3@github.com/masystems/cloud-lines.git',
                            self.target_dir)

            # update settings
            deployment.build_status = deployment.build_status + "\nCreated clone of Cloud-Lines"
            deployment.save()

            # copy in dependencies
            print('copy dependcies')
            for dep in self.dependency_packages:
                fullpath = os.path.join('/opt/dependcies/', dep)
                if os.path.isfile(fullpath):
                    shutil.copy(fullpath, self.target_dir)

            # update settings
            deployment.build_status = deployment.build_status + "\nAdded in some dependencies"
            deployment.save()

            # update zappa settings
            print('set zappa settings')
            template = self.env.get_template('zappa_settings.j2')
            with open(os.path.join(self.target_dir, 'zappa_settings.json'), 'w') as fh:
                fh.write(template.render(site_name=self.site_name))

            # update settings
            deployment.build_status = deployment.build_status + "\nCreated site configuration file"
            deployment.save()

            # create virtualenv
            print('creating virtual env')
            subprocess.Popen(['/usr/local/bin/virtualenv', '-p', 'python3', '/opt/instances/{}/venv'.format(self.site_name)])

            # update settings
            deployment.build_status = deployment.build_status + "\nCreated virtual environment"
            deployment.save()

            # wait for db to be created
            print('wating for DB to be created')
            waiter = client.get_waiter("db_instance_available")
            waiter.wait(DBInstanceIdentifier=self.site_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60}, )

            # update settings
            deployment.build_status = deployment.build_status + "\nDatabase has been created"
            deployment.save()

            # get db endpoint
            print('getting db endpoint')
            details = client.describe_db_instances(DBInstanceIdentifier=self.site_name)
            db_host = details['DBInstances'][0]['Endpoint']['Address']

            # update settings
            deployment.build_status = deployment.build_status + "\nCaptured new database settings"
            deployment.save()

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

            # update settings
            deployment.build_status = deployment.build_status + "\nConnected site to database"
            deployment.save()

            # generate user data
            process = subprocess.Popen(['/usr/bin/python3', '/opt/cloudlines/cloud-lines/manage.py', 'dumpdata', 'auth.user'], stdout=subprocess.PIPE)
            stdout = process.communicate()[0]
            users = json.loads(stdout)
            for user in users:
                if user['pk'] == deployment.user.pk:
                    with open(os.path.join(self.target_dir, 'user.json'), 'w') as outfile:
                        json.dump(user, outfile)


            # wrap user.json in square brackets because django said so!
            with open(os.path.join(self.target_dir, 'user.json'), "r+") as original:
                data = original.read()

            with open(os.path.join(self.target_dir, 'user.json'), "w") as original:
                original.write('[{}]'.format(data))

            # update settings
            deployment.build_status = deployment.build_status + "\nCaptured users settings"
            deployment.save()

            # run commands inside the venv
            subprocess.Popen(['/opt/venv.sh',
                              # $SITE_NAME
                              self.site_name,
                              # $USERNAME
                              str(deployment.user.username),
                              # $SERVICE_PK
                              str(deployment.attached_service.service.pk),
                              # $STRIPE_ID
                              deployment.user_detail.stripe_id,
                              # $SITE_MODE
                              deployment.attached_service.site_mode,
                              # $ANIMAL_TYPE
                              deployment.attached_service.animal_type,])

            # update settings
            deployment.build_status = deployment.build_status + "\nNew Cloud-Lines site build complete!"
            deployment.save()

            # update settings
            deployment.build_state = 'complete'
            deployment.save()

            # wait for domain to come up
            while True:
                domain = 'https://{}.cloud-lines.com'.format(deployment.subdomain)
                request = requests.get(domain)
                if request.status_code == 200:
                    print('Web site exists')
                    # send mail
                    msg = """Your site is now live at <a href="{}">{}</a>
                    
                    Enjoy your new Cloud-Lines instance!"""
                    # send to user
                    send_mail('Your Cloud-Lines instance is live!', deployment.user.username, msg, send_to=deployment.user.email)

                    # send to admin
                    send_mail('Your Cloud-Lines instance is live!', deployment.user.username, msg)
                    break
                else:
                    print('Web site does not exist')


if __name__ == '__main__':
    lt = LargeTier()
    lt.deploy()
