#!/usr/bin/python
"""
Import StepSpec entries from active ItemSpec records.

This helper populates StepSpec objects based on existing ItemSpec data.
"""

import bin_functions

bin_functions.setup_paths()
from gchub_db.apps.workflow.models import ItemSpec, StepSpec

current_specs = ItemSpec.objects.filter(active=True)  # [:5]

for x in current_specs:
    # Plant Review
    stepspec = StepSpec()
    stepspec.itemspec = x
    stepspec.num_colors = x.num_colors
    stepspec.template_horizontal = x.template_horizontal
    stepspec.template_vertical = x.template_vertical
    stepspec.step_around = x.step_around
    stepspec.step_across = x.step_across
    stepspec.num_blanks = x.num_blanks
    stepspec.save()
