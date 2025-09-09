#!/usr/bin/env python
"""Transfers all associated items from one ItemCatalog object to another."""

# Setup the Django environment
import bin_functions

bin_functions.setup_paths()
# Back to the ordinary imports
from django.template import loader

from gchub_db.includes import general_funcs

t = loader.get_template("emails/on_do_proof.txt")
c = {"somevar": "testing"}
general_funcs.send_info_mail("Subject here", t.render(c), ["gtaylor@l11solutions.com"])
