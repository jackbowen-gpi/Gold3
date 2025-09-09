"""QAD Data - Imports data from QAD in order to display/search in GOLD."""

from django.db import models

# from gchub_db.apps.workflow.models.general import ItemCatalog


class QAD_PrintGroups(models.Model):
    """List of PrintGroup names from QAD."""

    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "QAD Print Group"
        verbose_name_plural = "QAD Print Groups"

    def __str__(self):
        return self.name + "-" + self.description


class QAD_CasePacks(models.Model):
    """List of PrintGroup names from QAD."""

    size = models.ForeignKey("workflow.ItemCatalog", on_delete=models.CASCADE)
    case_pack = models.IntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "QAD Case Pack"
        verbose_name_plural = "QAD Case Packs"

    def __str__(self):
        return str(self.size) + ": " + str(self.case_pack)
