from collections import deque

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import Context
from django.urls import reverse
from django.utils import timezone

from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.joblog.models import JobLog
from gchub_db.apps.qc.models import (
    RESPONSE_TYPE_NA,
    RESPONSE_TYPE_NORESPONSE,
    RESPONSE_TYPE_OK,
    RESPONSE_TYPE_WHOOPS,
    QCResponse,
    QCResponseDoc,
    QCWhoops,
)


def create_review_and_redirect(request, qcdoc_id):
    """
    Creates a QCResponseDoc and sets its parent to the specified master QC.
    Redirects the browser to the QC editor instance for the created review QC.
    """
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)
    new_qc = qcdoc.create_review_qc(request.user)
    return HttpResponseRedirect(reverse("qc_edit_qc", args=[new_qc.id]))


def edit_qc(request, qcdoc_id):
    """
    This is where the bulk of the QC process takes place. The QC Editor is
    the interface in which artists can review items.
    """
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)
    # Build the context for rendering the QC Category description and the
    # question text.
    desc_context = Context({"qcdoc": qcdoc})

    # Store the parsed description value of each QCResponse's category's
    # description attribute. The data structure 'deque' acts as a standard
    # FIFO stack in this case.
    qcr_descriptions = deque()
    qcr_questions = deque()

    # Start pushing stuff on to the stacks.
    for qcr in qcdoc.qcresponse_set.all():
        desc = qcr.category.get_description_template()
        # Push the deescription to the end of the stack.
        qcr_descriptions.append(desc.render(desc_context))

        for question in qcr.get_workflow_questions():
            qtemp = question.get_question_template()
            qcr_questions.append(qtemp.render(desc_context))

    pagevars = {
        "qcdoc": qcdoc,
        "response_values": {
            "noresponse": RESPONSE_TYPE_NORESPONSE,
            "ok": RESPONSE_TYPE_OK,
            "whoops": RESPONSE_TYPE_WHOOPS,
            "na": RESPONSE_TYPE_NA,
        },
        "qcr_descriptions": qcr_descriptions,
        "qcr_questions": qcr_questions,
    }

    return render(request, "qc/qc_editor.html", context=pagevars)


def view_qc(request, qcdoc_id):
    """
    The QC Viewer shows a QC's responses and lets the artist or another person
    respond to Whoopses.
    """
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)

    if request.GET:
        resolve_id = request.GET.get("resolve", False)
        if resolve_id:
            whoops = QCWhoops.objects.get(id=int(resolve_id))
            whoops.resolution_date = timezone.now()
            whoops.save()

        invalidate_id = request.GET.get("invalidate", False)
        if invalidate_id:
            whoops = QCWhoops.objects.get(id=int(invalidate_id))
            whoops.resolution_date = timezone.now()
            whoops.is_valid = False
            whoops.artist_comments = request.GET.get("reason", "")
            whoops.save()

    pagevars = {
        "qcdoc": qcdoc,
        "response_values": {
            "noresponse": RESPONSE_TYPE_NORESPONSE,
            "ok": RESPONSE_TYPE_OK,
            "whoops": RESPONSE_TYPE_WHOOPS,
            "na": RESPONSE_TYPE_NA,
        },
    }

    return render(request, "qc/qc_viewer.html", context=pagevars)


def finish_qc(request, qcdoc_id):
    """This view handles the finishing and submitting of a QCResponseDoc."""
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)

    qcdoc.review_date = timezone.now()
    qcdoc.save()

    if qcdoc.parent:
        joblog_type = joblog_defs.JOBLOG_TYPE_REVIEW_QC_SUBMITTED
        joblog_text = "Review QC has been submitted by %s" % (request.user)
        whoops_found = qcdoc.get_unresolved_whoops().count()

        growl_title = "%s QC Reviewed" % qcdoc.job
        if whoops_found > 0:
            growl_text = "%s has reviewed your QC and found %s problems." % (
                request.user,
                whoops_found,
            )
        else:
            growl_text = "%s has reviewed your QC and found no problems." % (request.user)

        qcdoc.job.growl_at_artist(growl_title, growl_text, pref_field="growl_hear_jdf_processes")
    else:
        joblog_type = joblog_defs.JOBLOG_TYPE_QC_SUBMITTED
        joblog_text = "Initial QC has been submitted."

    joblog = JobLog(type=joblog_type, job=qcdoc.job, log_text=joblog_text)
    joblog.save()

    pagevars = {"qcdoc": qcdoc}

    return render(request, "qc/finished.html", context=pagevars)


def ajax_set_response_type(request, qcresponse_id):
    """Approves a QCResponse via AJAX."""
    qcresponse = get_object_or_404(QCResponse, id=qcresponse_id)

    # Store the comment.
    comment = request.POST.get("comment", None)
    response_type = request.POST["response_type"]

    # If no comment is provided, we've got a problem.
    if request.POST and comment and comment.strip() != "":
        qcresponse.comments = comment
    else:
        qcresponse.comments = ""

    qcresponse.response = int(response_type)
    qcresponse.save()
    return HttpResponse("success")


def ajax_whoops_report(request, qcresponse_id):
    """Reports a "Whoops!" on a QCResponse via AJAX."""
    # Store the comment.
    comment = request.POST.get("comment", False)

    # If no comment is provided, we've got a problem.
    if not request.POST or not comment or comment.strip() == "":
        return HttpResponse("no_comment")

    # Set the response type on this QCResponse to Whoops!
    qcresponse = get_object_or_404(QCResponse, id=qcresponse_id)
    qcresponse.response = RESPONSE_TYPE_WHOOPS
    # Comments and Whoops are mutually exclusive.
    qcresponse.comments = None
    qcresponse.save()

    # Save the Whoops!
    whoops = QCWhoops(qc_response=qcresponse, details=comment)
    whoops.save()

    return HttpResponse(comment)


def ajax_whoops_delete(request, qcwhoops_id):
    """Deletes a QCWhoops."""
    qcwhoops = get_object_or_404(QCWhoops, id=qcwhoops_id)
    qc_response = qcwhoops.qc_response
    num_whoops = qc_response.qcwhoops_set.count()
    qcwhoops.delete()

    if num_whoops == 1:
        # No more whoops remaining, go back to no response.
        qc_response.response = RESPONSE_TYPE_NORESPONSE
        qc_response.save()
    return HttpResponse("success")


def ajax_whoops_get_div(request, qcresponse_id):
    """Returns the HTML list of whoopses for a QCResponse."""
    qcresponse = get_object_or_404(QCResponse, id=qcresponse_id)
    pagevars = {"qcresponse": qcresponse}
    return render(request, "qc/whoops_div.html", context=pagevars)


###############################################################
###############################################################
###############################################################
###############################################################

# New Calls for QC layout


def create_review_and_redirect2(request, qcdoc_id):
    """
    Creates a QCResponseDoc and sets its parent to the specified master QC.
    Redirects the browser to the QC editor instance for the created review QC.
    """
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)
    new_qc = qcdoc.create_review_qc(request.user)
    return HttpResponseRedirect(reverse("qc_edit_qc2", args=[new_qc.id]))


def edit_qc2(request, qcdoc_id):
    """
    This is where the bulk of the QC process takes place. The QC Editor is
    the interface in which artists can review items.
    """
    qcdoc = get_object_or_404(QCResponseDoc, id=qcdoc_id)
    # Build the context for rendering the QC Category description and the
    # question text.
    desc_context = Context({"qcdoc": qcdoc})

    # Store the parsed description value of each QCResponse's category's
    # description attribute. The data structure 'deque' acts as a standard
    # FIFO stack in this case.
    qcr_descriptions = deque()
    qcr_questions = deque()

    qcResponseList = []
    qcWorkflow = qcdoc.job.workflow.name

    # Start pushing stuff on to the stacks.
    for qcr in qcdoc.qcresponse_set.all():
        #####################################################
        # This if statement checks to see if the QC is for Foodservice
        # If so, exclude the Beverage specific descriptions based on id (can be found in the Admin interface)
        # This is done to hide unneeded tabs from FSB

        if qcWorkflow == "Foodservice" or qcWorkflow == "Carton":
            if qcr.category.id == 9 or qcr.category.id == 11:
                qcr.response = 3
                continue

        if qcWorkflow == "Beverage":
            if qcr.category.id == 12:
                qcr.response = 3
                continue

        desc = qcr.category.get_description_template()

        # Push the description to the end of the stack.
        qcr_descriptions.append(desc.render(desc_context))

        for question in qcr.get_workflow_questions():
            qtemp = question.get_question_template()
            qcr_questions.append(qtemp.render(desc_context))
        qcResponseList.append(qcr)

    ###############################################################
    # Checks to see which version of the QC we are working with...
    # ie: Proof, Revision, Final File

    # list = all of the QCResponse items.
    list = qcdoc.items.all()
    for item in list:
        if (not item.final_file_date()) and item.current_proof_date() and item.is_approved() and (not item.current_revision()):
            qc_type = "Final File"
            break
        elif item.current_revision():
            qc_type = "Revision"
            break
        elif not item.current_proof_date():
            qc_type = "Proof"
            break
        else:
            qc_type = "Default"

    pagevars = {
        "qcdoc": qcdoc,
        "qcResponseList": qcResponseList,
        "response_values": {
            "noresponse": RESPONSE_TYPE_NORESPONSE,
            "ok": RESPONSE_TYPE_OK,
            "whoops": RESPONSE_TYPE_WHOOPS,
            "na": RESPONSE_TYPE_NA,
        },
        "qcr_descriptions": qcr_descriptions,
        "qcr_questions": qcr_questions,
        "qc_type": qc_type,
    }

    return render(request, "qc/qc_editor2.html", context=pagevars)
