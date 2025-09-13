"""Create a development superuser and dump basic fixtures for local use."""

import os
import threading

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()
from django.contrib.auth import get_user_model

# Small script timeout helper: set SCRIPT_TIMEOUT_SECONDS in env to override.
SCRIPT_TIMEOUT_SECONDS = int(os.environ.get("SCRIPT_TIMEOUT_SECONDS", "300"))  # default 5 minutes


def _exit_proc():
    print(f"Script timed out after {SCRIPT_TIMEOUT_SECONDS} seconds, exiting.")
    os._exit(2)


# Start a daemon timer; it will terminate the process if this script runs longer
_timer = threading.Timer(SCRIPT_TIMEOUT_SECONDS, _exit_proc)
_timer.daemon = True
_timer.start()

User = get_user_model()
username = "devadmin"
email = "devadmin@example.local"
password = "pass123"
user = User.objects.filter(username=username).first()
if not user:
    user = User.objects.create_superuser(username=username, email=email, password=password)
    user.first_name = "dev"
    user.last_name = "admin"
    user.save()
    print("created superuser devadmin with name dev admin")
else:
    print("superuser devadmin exists; not modified")
from django.core import management

management.call_command(
    "dumpdata",
    "auth.user",
    "sites.site",
    output=os.path.join(os.path.dirname(__file__), "..", "fixtures_initial.json"),
)
print("dumped fixtures to fixtures_initial.json")

# Cancel the timer when finished
try:
    _timer.cancel()
except Exception:
    pass
