"""Table-level operations for the workflow app."""

from django.db import models


class ItemManager(models.Manager):
    def not_deleted(self):
        """
        Returns a list of Item objects that have not been soft deleted (had
        their is_deleted field set to True).
        """
        return self.filter(is_deleted=False)

    def get_queryset(self):
        return super(ItemManager, self).get_queryset().filter(is_deleted=False)


class JobManager(models.Manager):
    def get_queryset(self):
        return super(JobManager, self).get_queryset().filter(is_deleted=False)
