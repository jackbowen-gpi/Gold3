from django.contrib.contenttypes.models import ContentType
from django.db import models


class QCResponseDocManager(models.Manager):
    def start_qc_for_items(self, items, reviewer, parent=None):
        """This is the function that should be used to start QCs. It creates the
        QCResponseDoc for the QC, populates the items list, and creates all of
        the QCResponse objects through a method call.

        items: (QuerySet/list) The Item objects to QC.
        reviewer: (User) The person doing the QC.
        parent: (QCResponseDoc) If this is not the first QC, point to first QC.
        """
        # Avoid the circular import.
        QCResponseDoc = ContentType.objects.get(
            app_label="qc", model="qcresponsedoc"
        ).model_class()

        new_qc = QCResponseDoc(parent=parent, reviewer=reviewer)
        # The QCDoc must be saved before we can mess with the items field.
        new_qc.job = items[0].job
        new_qc.save()

        # Add everything specified to the items list.
        for item in items:
            new_qc.items.add(item)

        # Create the QCResponse objects for this QCDoc.
        new_qc.populate_new_qc()

        # For convenience.
        return new_qc
