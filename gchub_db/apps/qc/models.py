from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.template import Template

from gchub_db.apps.qc.managers import QCResponseDocManager
from gchub_db.apps.workflow.models import Item, Job


class QCCategory(models.Model):
    """QC Categories serve to group sets of QCQuestions. Users approve or reject
    QCCategories instead of addressing each question.
    """

    # This shows up on the header of each QC section.
    title = models.CharField(max_length=255)
    # This is more for internal documentation for QC managers.
    description = models.TextField(blank=True, null=True)
    # Determines in what order the users address this category.
    order = models.IntegerField()

    def __str__(self):
        return "%s" % (self.title,)

    class Meta:
        ordering = ["order"]
        verbose_name = "QC Category"
        verbose_name_plural = "QC Categories"

    def get_description_template(self):
        """Returns a template system Template object for the category's description."""
        return Template(self.description)


class QCQuestionDefinition(models.Model):
    """Questions are individual line items grouped beneath a QCCategory. They
    are not responded to individually. Users approve or reject QCCategories.
    """

    # This determines what category the question is rendered beneath.
    category = models.ForeignKey(QCCategory, on_delete=models.CASCADE)
    # Questions are specific to one workflow.
    workflow = models.ForeignKey(Site, on_delete=models.CASCADE)
    question = models.TextField()
    # This points to Wiki documentation on what to check for.
    help_url = models.URLField(blank=True, null=True)
    # Determines in what order the questions are displayed.
    order = models.IntegerField()

    def __str__(self):
        return "%s (%s)" % (self.question, self.workflow.name)

    class Meta:
        ordering = ["workflow", "category", "order"]
        verbose_name = "QC Question Definition"
        verbose_name_plural = "QC Question Definitions"

    def get_question_template(self):
        """Returns a template system Template object for the question."""
        return Template(self.question)


class QCResponseDoc(models.Model):
    """This model is what all of the QCResponse objects point to for grouping.
    It is best to think of a QCResponseDoc as one individual QC instance.

    A QCResponseDoc with a None value for 'parent' is the first QC in the
    series of at least two. Any QCs following the initial one should set
    parent to the first QCResponseDoc done by the artist.
    """

    # If this is not the first QC in a series, point to the first one.
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, editable=False
    )
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item, editable=False)
    # This is a convenience de-normalization. Make sure to keep it up to date.
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, blank=True, null=True, editable=False
    )
    # This is None until the QC is finished.
    review_date = models.DateTimeField(blank=True, null=True)

    # QC Creation and other things are brought in here.
    objects = QCResponseDocManager()

    class Meta:
        ordering = ["-review_date"]
        verbose_name = "QC Reponse Document"
        verbose_name_plural = "QC Reponse Documents"

    def __str__(self):
        # Let us know if this is a first QC or now.
        if self.parent:
            qc_designator = "(Redundant QC)"
        else:
            qc_designator = "(Artist QC)"

        return "%d %s by %s %s" % (
            self.job.id,
            self.job.name,
            self.reviewer,
            qc_designator,
        )

    def populate_new_qc(self):
        """Performs some setup work on new QCResponseDoc objects. For example,
        creates QCResponse objects for all of the categories in advance, to
        make the QC Editing views' job a lot easier.
        """
        # Prevent duplication.
        self.qcresponse_set.all().delete()
        # Create the QCResponse documents in the correct order using the
        # default sorting.
        if self.parent:
            # If we are creating a review QC, copy from the QCResponse objects
            # instead of the vanilla QCCategory to transfer some data.
            for qcr in self.parent.qcresponse_set.all():
                new_response = QCResponse(category=qcr.category, qcdoc=self)
                if qcr.response == RESPONSE_TYPE_NA:
                    # For things marked N/A, they should show up to the review
                    # QC'er as N/A.
                    new_response.response = RESPONSE_TYPE_NA
                new_response.save()
        else:
            # Copy details straight from QCCategory objects since no parent
            # exists.
            for cat in QCCategory.objects.all():
                new_response = QCResponse(category=cat, qcdoc=self)
                new_response.save()

    def create_review_qc(self, reviewer):
        """Creates a QCResponseDoc and sets its parent to this QC. This done for
        Review QCs (not done by the artist).
        """
        items = self.items.all()
        return QCResponseDoc.objects.start_qc_for_items(items, reviewer, parent=self)

    def get_unresolved_whoops(self):
        """Returns all QCWhoops objects on this QC document that have not yet been
        resolved via fixing the noted problem or invalidation of the Whoops.
        """
        return QCWhoops.objects.filter(
            qc_response__qcdoc=self, resolution_date__isnull=True
        )

    def is_whoopsless(self):
        """Checks to make sure the review is free of unresolved QCWhoops."""
        if self.get_unresolved_whoops():
            # QuerySet has entries, which means there are outstanding whoops.
            return False
        # Whoopsless!
        return True

    def get_finalized_children(self):
        """Returns child QCResponseDoc objects that have been finalized (submitted)."""
        return self.qcresponsedoc_set.filter(review_date__isnull=False)


# The reviewer hasn't responded to this QCCategory yet.
RESPONSE_TYPE_NORESPONSE = 0
# The reviewer gives this section the go-ahead.
RESPONSE_TYPE_OK = 1
# Reviewer found a problem, see whoops fields for details.
RESPONSE_TYPE_WHOOPS = 2
# Reviewer says this section does not apply to the item/qc.
RESPONSE_TYPE_NA = 3

RESPONSE_TYPES = (
    (RESPONSE_TYPE_NORESPONSE, "No Response"),
    (RESPONSE_TYPE_OK, "OK"),
    (RESPONSE_TYPE_WHOOPS, "Whoops!"),
    (RESPONSE_TYPE_NA, "N/A"),
)


class QCResponse(models.Model):
    """This is an individual response to a QCCategory."""

    category = models.ForeignKey(QCCategory, on_delete=models.CASCADE)
    qcdoc = models.ForeignKey(QCResponseDoc, on_delete=models.CASCADE)
    # See the response table above, but this can be several different things.
    response = models.IntegerField(
        choices=RESPONSE_TYPES, default=RESPONSE_TYPE_NORESPONSE
    )
    comments = models.TextField(blank=True, null=True)
    # Has the artist been notified of QC completion?
    artist_notified = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        verbose_name = "QC Response"
        verbose_name_plural = "QC Responses"

    def __str__(self):
        return self.category.title

    def get_parent_qcresponse_comments(self):
        """In the case of a second or third (or fourth) QC, look to the parent
        QC on the corresponding QCResponse object for artist comments.
        """
        if self.qcdoc.parent:
            parent_qcr = self.qcdoc.parent.qcresponse_set.get(category=self.category)
            return parent_qcr.comments

        # Nothing doing.
        return False

    def get_active_whoops_qset(self):
        """Returns a QuerySet of the current Whoops entries that are in need
        of attention from the artist.
        """
        return self.qcwhoops_set.filter(resolution_date__isnull=True)

    def get_response_icon_filename(self):
        """Returns the filename for the icon that will show up on tabs for the
        QCResponse's response attribute.
        """
        filename = ""
        if self.response == RESPONSE_TYPE_NORESPONSE:
            filename = "help.png"
        elif self.response == RESPONSE_TYPE_OK:
            filename = "accept.png"
        elif self.response == RESPONSE_TYPE_WHOOPS:
            filename = "error.png"
        elif self.response == RESPONSE_TYPE_NA:
            filename = "emoticon_tongue.png"
        else:
            filename = "help.png"

        return "img/icons/%s" % filename

    def get_workflow_questions(self):
        """Returns all of a Category's questions based on the specified workflow.

        workflow: (Site) The workflow to filter by.
        """
        return self.category.qcquestiondefinition_set.filter(
            workflow=self.qcdoc.job.workflow
        )


class QCWhoops(models.Model):
    """In the event that an error is found on a redundant (second or more) QC
    that the artist did not catch, the reviewer will report a Whoops.
    """

    # The QCResponse object this is Whoopsing.
    qc_response = models.ForeignKey(QCResponse, on_delete=models.CASCADE)
    # Details from the reviewer as to what is wrong.
    details = models.TextField()
    # If this is False, disregard this Whoops!
    is_valid = models.BooleanField(default=True)
    # When the Whoops! was first reported by the reviewer.
    reported_date = models.DateTimeField(auto_now_add=True)
    # If the artist provides any comments when invalidating or resolving a
    # Whoops!, store them here.
    artist_comments = models.TextField(blank=True, null=True)
    # This solves as a tracker and a Bool to determine what has been resolved.
    resolution_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Whoops!"
        verbose_name_plural = "Whoopsies!"
