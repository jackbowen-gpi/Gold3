import json
import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

django.setup()

out = json.dumps(settings.DATABASES, default=str, indent=2)
open(r"C:\Dev\Gold\gchub_db\dev\db_settings_active.json", "w").write(out)
print("wrote dev/db_settings_active.json")
