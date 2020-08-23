#!/usr/bin/python3
import django
import sys
import os
import shutil
import random
import string
import subprocess
import requests
from requests.adapters import HTTPAdapter
from jinja2 import Environment, FileSystemLoader
import boto3
from botocore.config import Config
from git import Repo
from time import sleep
import json
import socket

if socket.gethostname() == "X303":
    sys.path.append('/home/marco/projects/masys/cloudlines/cloud-lines')
else:
    sys.path.append('/opt/cloudlines/cloud-lines')

os.environ["DJANGO_SETTINGS_MODULE"] = "cloudlines.settings"
django.setup()

from cloud_lines.models import LargeTierQueue
from account.views import send_mail


class BuildSubscription:
    def __init__(self, site):
        self.site = site
        self.site_name = self.site.subdomain
        # Generate passwords
        self.django_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(50)])
        self.db_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])
        self.db_username = 'pedigreedbuser'

        self.boto_config = Config(retries=dict(max_attempts=20))

        #self.dependency_packages = os.listdir('/opt/dependencies/')

        if socket.gethostname() == "X303":
            self.target_dir = f'/home/marco/projects/masys/cloud-lines/subscriptions/{self.site_name}'
        else:
            self.target_dir = f'/opt/subscriptions/{self.site_name}'

        # set template dir root
        self.env = Environment(loader=FileSystemLoader(self.target_dir))

        self.client = boto3.client(
            'rds', region_name='eu-west-2', config=self.boto_config
        )

    def update_progress(self, state=None, status=None, percent=None):
        if state:
            self.site.build_state = state
            print(state)
        if status:
            self.site.build_status = status
            print(status)
        if percent:
            self.site.percentage_complete = percent
            print(percent)
        self.site.save()

    def deploy(self):
        # update settings
        self.update_progress(status='Captured settings', state='building', percent=10)
        sleep(10)

        self.create_datebase()
        self.clone_repo()
        self.wait_for_db_creation()
        self.get_db_endpoint()
        self.configure_local_settings()
        self.capture_user_data()

        ### ECR ECS stuff ###

        #self.wait_domain_initialisation()

    def create_datebase(self):
        # create database
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
        new_db = self.client.create_db_instance(**db_vars)

        # update settings
        self.update_progress(status="Initiating database creation", percent=20)
        sleep(10)

    def clone_repo(self):
        # clone repo
        print('clone repo')
        Repo.clone_from('https://masystems:H5m6RZK0AVh3IumrybH3@github.com/masystems/cloud-lines.git',
                        self.target_dir)

        # update settings
        self.update_progress(status="Created clone of Cloud-Lines", percent=30)
        sleep(10)

    def copy_dependencies(self):
        """
        Legacy code
        :return:
        """
        # copy in dependencies
        print('copy dependcies')
        for dep in self.dependency_packages:
            fullpath = os.path.join('/opt/dependcies/', dep)
            if os.path.isfile(fullpath):
                shutil.copy(fullpath, self.target_dir)

        # update settings
        self.update_progress(status="Added in some dependencies", percent=40)
        sleep(10)

    def wait_for_db_creation(self):
        # wait for db to be created
        print('wating for DB to be created')
        waiter = self.client.get_waiter("db_instance_available")
        waiter.wait(DBInstanceIdentifier=self.site_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60}, )

        # update settings
        self.update_progress(status="Database has been created", percent=70)
        sleep(10)

    def get_db_endpoint(self):
        # get db endpoint
        print('getting db endpoint')
        details = self.client.describe_db_instances(DBInstanceIdentifier=self.site_name)
        self.db_host = details['DBInstances'][0]['Endpoint']['Address']

        # update settings
        self.update_progress(status="Captured new database settings", percent=80)
        sleep(10)

    def configure_local_settings(self):
        # update local settings
        template = self.env.get_template('cloudlines/local_settings.j2')
        with open(os.path.join(self.target_dir, 'cloudlines/local_settings.py'), 'w') as fh:
            fh.write(template.render(site_name=self.site_name,
                                     site_mode='hierarchy',
                                     django_password=self.django_password,
                                     db_name=self.site_name,
                                     db_username=self.db_username,
                                     db_password=self.db_password,
                                     db_host=self.db_host))

        # update settings
        self.update_progress(status="Connected site to database", percent=90)
        sleep(10)

    def capture_user_data(self):
        # generate user data
        if socket.gethostname() == "X303":
            process = subprocess.Popen(['/home/marco/projects/masys/cloudlines/venv/bin/python', '/home/marco/projects/masys/cloudlines/cloud-lines/manage.py', 'dumpdata', 'auth.user'], stdout=subprocess.PIPE)
        else:
            process = subprocess.Popen(['/usr/bin/python3', '/opt/cloudlines/cloud-lines/manage.py', 'dumpdata', 'auth.user'], stdout=subprocess.PIPE)
        stdout = process.communicate()[0]
        users = json.loads(stdout)
        for user in users:
            if user['pk'] == self.site.user.pk:
                with open(os.path.join(self.target_dir, 'user.json'), 'w') as outfile:
                    json.dump(user, outfile)

        # wrap user.json in square brackets because django said so!
        with open(os.path.join(self.target_dir, 'user.json'), "r+") as original:
            data = original.read()

        with open(os.path.join(self.target_dir, 'user.json'), "w") as original:
            original.write('[{}]'.format(data))

        # update settings
        self.update_progress(status="Captured users settings", percent=95)
        sleep(10)

    def venv(self):
        """
        Depreciated code
        :return:
        """
        # run commands inside the venv
        subprocess.Popen(['/opt/venv.sh',
                          # $SITE_NAME
                          self.site_name,
                          # $USERNAME
                          str(self.site.user.username),
                          # $SERVICE_PK
                          str(self.site.attached_service.service.pk),
                          # $STRIPE_ID
                          self.site.user_detail.stripe_id,
                          # $SITE_MODE
                          self.site.attached_service.site_mode,
                          # $ANIMAL_TYPE
                          self.site.attached_service.animal_type,])

        # update settings
        self.update_progress(status="New Cloud-Lines site build complete!", percent=100)
        sleep(10)

        # update settings
        self.site.build_state = 'complete'
        self.site.save()

    def wait_domain_initialisation(self):
        # wait for domain to come up
        domain = 'https://{}.cloud-lines.com'.format(self.site.subdomain)
        status = ''
        for x in range(0, 500):
            try:
                session = requests.Session()
                session.mount(domain, HTTPAdapter(max_retries=1))
                request = session.get(domain, timeout=5)

                if request.status_code == 200:
                    print('Web site exists')
                    # send mail
                    msg = """Your site is now live at <a href="{}">{}</a>
                    Enjoy your new Cloud-Lines instance!""".format(domain, domain)
                    # send to user
                    send_mail('Your new Cloud-Lines instance is live!', self.site.user.username, msg, send_to=self.site.user.email)
                    # send to admin
                    send_mail('Your new Cloud-Lines instance is live!', self.site.user.username, msg)
                    break
                else:
                    print('Web site does not exist')
            except requests.exceptions.ConnectionError:
                status = "DOWN"
            except requests.exceptions.HTTPError:
                status = "HttpError"
            except requests.exceptions.ProxyError:
                status = "ProxyError"
            except requests.exceptions.Timeout:
                status = "TimeoutError"
            except requests.exceptions.ConnectTimeout:
                status = "connectTimeout"
            except requests.exceptions.ReadTimeout:
                status = "ReadTimeout"
            except requests.exceptions.TooManyRedirects:
                status = "TooManyRedirects"
            except requests.exceptions.MissingSchema:
                status = "MissingSchema"
            except requests.exceptions.InvalidURL:
                status = "InvalidURL"
            except requests.exceptions.InvalidHeader:
                status = "InvalidHeader"
            except requests.exceptions.URLRequired:
                status = "URLmissing"
            except requests.exceptions.InvalidProxyURL:
                status = "InvalidProxy"
            except requests.exceptions.RetryError:
                status = "RetryError"
            except requests.exceptions.InvalidSchema:
                status = "InvalidSchema"
            print(status)
            sleep(5)

if __name__ == '__main__':
    waiting_requests = LargeTierQueue.objects.filter(build_state='waiting')

    for site in waiting_requests.all():
        lt = BuildSubscription(site)
        lt.deploy()
