from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

# Impact levels are a way to describe whether a change is considered major or
# minor.
IMPACT_LEVELS = (
    (0, "Low"),
    (1, "Medium"),
    (2, "High"),
)

# This describes what kind of change is being announced.
CHANGE_TYPES = (
    (0, "Feature Enhancement"),
    (1, "New Feature"),
    (1, "Bug Fix"),
)

COOL_POINTS_TYPES = (
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
    (6, "6"),
    (7, "7"),
    (8, "8"),
    (9, "9"),
    (10, "10"),
)


class CodeChange(models.Model):
    """
    This model tracks incremental changes to GOLD over time so that users can
    see what is being worked on. A lot of new features are implemented and
    improvements are being made without ever being noticed by users.
    """

    change = models.TextField(help_text="A description of the change, in terms that the end users can understand.")
    workflows_affected = models.ManyToManyField(Site, help_text="Which workflows are affected by the change.")
    change_type = models.IntegerField(choices=CHANGE_TYPES)
    impact_level = models.IntegerField(choices=IMPACT_LEVELS, help_text="How big or important of a change this is.")
    cool_points = models.PositiveSmallIntegerField(choices=COOL_POINTS_TYPES, default=5, help_text="How cool this change is.")
    creation_date = models.DateTimeField(
        default=timezone.now,
        help_text="The post date. May be changed to affect sorting.",
    )
    growl_date = models.DateTimeField(blank=True, null=True)
