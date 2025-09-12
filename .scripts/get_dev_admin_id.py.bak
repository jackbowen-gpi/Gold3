import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django

django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DEV_ADMIN_USER", "dev_admin")
user = User.objects.filter(username=username).first()
if not user:
    print("NO_USER")
    sys.exit(2)
print(user.pk)
