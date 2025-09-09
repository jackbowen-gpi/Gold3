"""This is the mod_wsgi configuration that apache2 uses to interface with Django and the application."""

import os
import sys

# This will quiet the errors when printing but is not ideal.
# sys.stdout = sys.stderr

# Calculate the path based on the location of the WSGI script.
apache_configuration = os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
includes = os.path.join(project, "includes")
workspace = os.path.dirname(project)

if project not in sys.path:
    sys.path.insert(0, project)
if includes not in sys.path:
    sys.path.insert(0, includes)
# Directory immediately above gchub_db
if workspace not in sys.path:
    sys.path.insert(0, workspace)

os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
