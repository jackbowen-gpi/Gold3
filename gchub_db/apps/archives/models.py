"""Houses information for old facility art file archives"""

from django.db import models

# Document types. Use these in logic code instead of referring to their numbers.
DOCTYPE_SCANNED_DOC = 0
DOCTYPE_APPROVAL_PROOF = 5
DOCTYPE_EMAIL = 10

DOCUMENT_TYPES = (
    (DOCTYPE_SCANNED_DOC, "Scanned Document"),
    (DOCTYPE_APPROVAL_PROOF, "Approval Proof"),
    (DOCTYPE_EMAIL, "Email"),
)


class KentonArchive(models.Model):
    """Foodservice art archives"""

    file = models.CharField(max_length=255)
    cd = models.CharField(max_length=255, blank=True)
    art_reference = models.CharField(max_length=255, blank=True)
    job_name = models.CharField(max_length=30255, blank=True)
    plates_ordered = models.DateField("Date Plates Ordered", null=True, blank=True)
    size = models.CharField(max_length=255, blank=True)
    item_number = models.CharField(max_length=255, blank=True)
    document_number = models.CharField(max_length=255, blank=True)


class RenMarkArchive(models.Model):
    """Beverage art archives"""

    item = models.CharField(max_length=255)
    size = models.CharField(max_length=255, blank=True)
    folder_creation = models.DateField("Date Folder Created", blank=True, null=True)
    # Currently a bulleted list.
    folder_items = models.TextField(blank=True)
