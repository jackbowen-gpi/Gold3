import os

# Configure to use Postgres dev DB like the seeder
os.environ.setdefault("USE_PG_DEV", "1")
os.environ.setdefault("DEV_DB_NAME", "gchub_dev")
os.environ.setdefault("DEV_DB_HOST", "localhost")
os.environ.setdefault("DEV_DB_PORT", "5432")
os.environ.setdefault("DEV_DB_USER", "postgres")
os.environ.setdefault("DEV_DB_PASSWORD", "postgres")
# Ensure Django settings module matches manage.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
from django.apps import apps

django.setup()

for m in apps.get_models():
    label = f"{m._meta.app_label}.{m.__name__}"
    if label.split(".")[0] in ("auth", "contenttypes", "sessions", "admin"):
        continue
    try:
        print(label, m.objects.count())
    except Exception as e:
        print(label, "ERR", str(e))
