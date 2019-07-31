import django
import sys
import os
sys.path.append('/opt/cloud-lines/cloud-lines')
os.environ["DJANGO_SETTINGS_MODULE"] = "cloudlines.settings"
django.setup()

from cloud_lines import LargeTierQueue

class LargeTier:
    def __init__(self):
        print('object created')
        queue = LargeTierQueue.objects.all()
        print(queue)


if __name__ == '__main__':
    lt = LargeTier()
