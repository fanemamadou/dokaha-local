import os, sys
from django.core.wsgi import get_wsgi_application

project_home = '/home/fane/dokaha'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dokaha.settings')
application = get_wsgi_application()
