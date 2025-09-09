import os
import os.path
import sys

# Setup the Django environment
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"
import os

# Back to the ordinary imports
from .colorbook_reader import EskoColorBook

# Only run this demo/test when the expected resource file exists. In our
# local/dev environment the production colorbook files live on a mounted
# workflow share; skip gracefully when absent.
try:
    cb = EskoColorBook("FSB_Pantone_Uncoated")
except Exception as exc:
    print("Esko color book not available; skipping demo:", exc)
else:
    print(cb)
    color = cb.get_color("Black 2")
    print(color)
    lab = color.get_lab_color_obj()
    print(lab)
