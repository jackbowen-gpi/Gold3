"""Beverage Billing/Invoice Views"""

from io import BytesIO

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from gchub_db.apps.bev_billing.models import BevInvoice
from gchub_db.includes import general_funcs
from gchub_db.includes.form_utils import JSONErrorForm
from gchub_db.includes.gold_json import JSMessage

from .bev_billing_funcs import generate_pdf_invoice


class BevInvoiceForm(ModelForm, JSONErrorForm):
    """Form to update invoice information -- used primarily by accounting."""

    qad_entered = forms.BooleanField(required=False, label="QAD Entry?")
    invoice_number = forms.CharField(required=False, max_length=12, widget=forms.TextInput(attrs={"size": "12"}))

    class Meta:
        model = BevInvoice
        fields = (
            "qad_entered",
            "invoice_number",
        )

    def __init__(self, *args, **kwargs):
        super(BevInvoiceForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            # If there's a QAD entry date, this has already been entered
            # in QAD.
            if self.instance.qad_entry_date:
                self.fields["qad_entered"].initial = True


@login_required
def view_invoice(request, invoice_id):
    """View a Beverage Invoice and it's details."""
    invoice = BevInvoice.objects.get(id=invoice_id)
    if request.method == "POST":  # save form
        form = BevInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            # Set initial state of send email.
            send_email = False
            # If QAD entry was checked, save the date into
            # the appropriate field.
            if not invoice.qad_entry_date:
                if form.cleaned_data.get("qad_entered", False):
                    invoice.qad_entry_date = general_funcs._utcnow_naive()
                    invoice.qad_entry_user = request.user
            # Same thing for tracking invoice entry dates/users.
            if not invoice.invoice_entry_date:
                if form.cleaned_data.get("invoice_number", False):
                    invoice.invoice_entry_date = general_funcs._utcnow_naive()
                    invoice.invoice_entry_user = request.user
                    send_email = True
            form.save()
            # Send out email with attached invoice PDF if invoice num was
            # Entered.
            if send_email:
                send_invoice_email(invoice.id)
            return HttpResponse(JSMessage("Saved."))
        else:
            return form.serialize_errors()
    else:
        form = BevInvoiceForm(instance=invoice)

        pagevars = {
            "page_title": "View Beverage Invoice",
            "invoice": invoice,
            "form": form,
        }

        return render(request, "bev_billing/view_invoice.html", context=pagevars)


class InvoiceQueue(ListView):
    """Listing of all pending invoices."""

    queryset = BevInvoice.objects.all().order_by("-creation_date")
    paginate_by = 25
    template_name = "bev_billing/search_results.html"

    def get_context_data(self, **kwargs):
        context = super(InvoiceQueue, self).get_context_data(**kwargs)
        context["page_title"] = "Beverage Invoices Pending"
        context["extra_link"] = general_funcs.paginate_get_request(self.request)
        return context

    # Require the user to be logged in to GOLD to view.
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InvoiceQueue, self).dispatch(*args, **kwargs)


def _get_invoice_pdf_object(invoice_id):
    """Get the data for the invoice PDF."""
    # We'll use BytesIO instead of saving files to the filesystem, that gets
    # to be pretty messy pretty quickly. BytesIO is a drop-in replacement
    # to file objects.
    invoice_pdf = BytesIO()
    # Pass the BytesIO object and the invoice ID off to the generation func.
    generate_pdf_invoice(invoice_id, invoice_pdf)
    # Read the entire contents of the BytesIO object into a string variable.
    data = invoice_pdf.getvalue()
    return data


def get_bev_invoice_pdf(request, invoice_id):
    """Get a beverage invoice PDF and return it to the browser."""
    invoice = BevInvoice.objects.get(id=invoice_id)
    data = _get_invoice_pdf_object(invoice_id)
    # Prepare a simple HTTP response with the BytesIO object as an attachment.
    response = HttpResponse(data, content_type="application/pdf")
    # This is the filename the server will suggest to the browser.
    filename = "invoice_%s.pdf" % invoice.invoice_number
    # The attachment header will make sure the browser doesn't try to
    # render the binary/ascii data.
    response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
    # Bombs away.
    return response


def send_invoice_email(invoice_id):
    """Create and send an email with the PDF of the invoice attached."""
    invoice = BevInvoice.objects.get(id=invoice_id)
    filename = "invoice_%s.pdf" % invoice.invoice_number
    data = _get_invoice_pdf_object(invoice_id)
    # Create an email message for attaching the invoice to.
    mail_list = []
    # admin #1 is james mccracken
    mail_list.append(settings.ADMINS[0][1])
    if not invoice.job.temp_printlocation.plant.name == "Plant City":
        # Plant city wants to review their invoices first so we don't send their
        # invoices directly to APMail@everpack.com.
        group_members = User.objects.filter(groups__name="EmailEverpackAPMail", is_active=True)
        for user in group_members:
            mail_list.append(user.email)
    # Include all users that should be copied on email.
    for user in invoice.job.temp_printlocation.plant.bev_controller.all():
        mail_list.append(user.email)

    email = EmailMessage(
        "Invoice %s" % str(invoice.invoice_number),
        "Invoice for job %s\n\n" % str(invoice.job),
        settings.EMAIL_FROM_ADDRESS,
        mail_list,
    )
    # Attach the file and specify type.
    email.attach(filename, data, "application/pdf")
    # Poof goes the mail.
    email.send(fail_silently=False)
    return "meh"
