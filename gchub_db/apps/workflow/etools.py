"""eTools operations module."""

import sys

import pyodbc
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template import loader
from django.urls import reverse
from gchub_db.apps.qad_data.models import QAD_PrintGroups
from gchub_db.apps.workflow.models import Item, ItemCatalog, Job, JobAddress
from gchub_db.includes import fs_api, general_funcs

from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.workflow import app_defs


# Mock cursor class for development when ETOOLS is disabled
class MockCursor:
    def __init__(self, data=None, description=None):
        self.data = data or []
        self.description = description or []
        self._fetched = False

    def execute(self, query):
        pass

    def fetchone(self):
        if not self._fetched and self.data:
            self._fetched = True
            return self.data[0]
        return None

    def fetchall(self):
        return self.data


# Mock row class for development
class MockRow:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Set to True to output verbose debugging info.
DEBUG = False
# If True, print a list of columns on each eTools job request.
PRINT_COLUMNS = False


# The workflow to set all incoming Jobs to. Don't do a DB query at import time;
# resolve lazily and defensively so manage/runserver can start in a fresh DB.
def _safe_get_site(name):
    try:
        return Site.objects.get(name=name)
    except Exception:
        return None


# Resolve workflow defensively.
WORKFLOW = _safe_get_site("Foodservice")
VALID_ETOOLS_JOB_STATUS = ("New", "Active", "Complete")
# A hard-wired value for the number of item# fields to check. This is silly,
# but will have to stand until/unless the eTools devs decide to follow
# sane relational database practices.
# TODO: Get the eTools devs to follow sane relational database practices.
ETOOLS_MAX_ITEMS = 9


def _get_conn_cursor():
    """
    In pyodbc, all SQL operations happen through the cursor. Get connected
    and return the cursor for use in a query.
    """
    # Check if ETOOLS is disabled for development
    if not getattr(settings, "ETOOLS_ENABLED", True):
        return MockCursor(), None

    connection = pyodbc.connect(settings.ETOOLS_ODBC_DSN)
    return connection.cursor(), connection


def get_server_version():
    """Queries for the server's version info."""
    # Check if ETOOLS is disabled for development
    if not getattr(settings, "ETOOLS_ENABLED", True):
        return "Mock SQL Server 2019 - Development Environment"

    cursor = _get_conn_cursor()[0]
    cursor.execute(
        "SELECT 'SQL Server ' + CONVERT(varchar(100),SERVERPROPERTY('productversion'))"
        " + ' - ' + CONVERT(varchar(100),SERVERPROPERTY('productlevel'))"
        " + ' - ' + CONVERT(varchar(100),SERVERPROPERTY('edition'))"
    )
    return cursor.fetchone()[0]


def _get_new_jobs():
    """
    Query for retrieving new jobs. Returns a cursor object, from which you
    may iterate through.
    """
    cursor = _get_conn_cursor()[0]
    cursor.execute("SELECT TOP 5 * FROM tb_FSAR_Data_SampArtReq WHERE Job_Status = 'New'" " ORDER BY Request_ID ASC")
    # cursor.execute(
    #     "SELECT TOP 10 * FROM tb_FSAR_Data_SampArtReq WHERE Request_ID = 104249"
    # )

    if PRINT_COLUMNS:
        # Show a list of columns + their data types.
        for column in cursor.description:
            print(column)

    return cursor


def get_job_by_request_id(request_id):
    """
    Query for retrieving new jobs. Returns a cursor object, from which you
    may iterate through.
    """
    request_id = int(request_id)

    # Check if ETOOLS is disabled for development
    if not getattr(settings, "ETOOLS_ENABLED", True):
        # Return mock data for development
        mock_data = MockRow(
            Request_ID=request_id,
            Customer_Name="Mock Customer Corp",
            Project_Description="Mock Project Description for Development",
            Job_Status="In Progress",
            Request_Date="2025-09-07",
            Due_Date="2025-09-14",
            Contact_Name="John Doe",
            Contact_Email="john.doe@mockcustomer.com",
            Contact_Phone="555-1234",
            Notes="This is mock ETOOLS data for development environment",
        )
        mock_description = [
            ("Request_ID",),
            ("Customer_Name",),
            ("Project_Description",),
            ("Job_Status",),
            ("Request_Date",),
            ("Due_Date",),
            ("Contact_Name",),
            ("Contact_Email",),
            ("Contact_Phone",),
            ("Notes",),
        ]
        return MockCursor(data=[mock_data], description=mock_description)

    cursor = _get_conn_cursor()[0]
    query = "SELECT TOP 1 * FROM tb_FSAR_Data_SampArtReq WHERE Request_ID = ?"
    cursor.execute(query, (request_id,))
    return cursor


def _set_etools_job_status(job_etools_id, job_status):
    """
    Query for retrieving new jobs. Returns a cursor object, from which you
    may iterate through.
    """
    if job_status not in VALID_ETOOLS_JOB_STATUS:
        print("Invalid status value.")
        sys.exit(1)
    cursor, connection = _get_conn_cursor()
    cursor.execute(
        "UPDATE tb_FSAR_Data_SampArtReq SET Job_Status = ? WHERE Request_ID = ?",
        (job_status, job_etools_id),
    )
    connection.commit()
    return cursor


def _get_etools_job_status(job_etools_id):
    """
    Query for retrieving new jobs. Returns a cursor object, from which you
    may iterate through.
    """
    cursor = _get_conn_cursor()[0]
    cursor.execute("SELECT Job_Status FROM tb_FSAR_Data_SampArtReq WHERE Request_ID = %d" % job_etools_id)

    return cursor


def _get_etools_field(job_etools_id, field):
    """
    Query for retrieving the value of a single field on an entry.

    Note:
    You do not want to fire these off in large numbers. If you need to update
    more than two or three fields at once, combine it into a single query!
    Each query creates a new connection and is therefore not something you
    want to do a lot.

    TODO: Add an optional argument to specify an existing connection/cursor.

    """
    cursor = _get_conn_cursor()[0]
    # Validate field name to prevent SQL injection
    allowed_fields = {
        "Request_ID",
        "Customer_Name",
        "Project_Description",
        "Job_Status",
        "Request_Date",
        "Due_Date",
        "Contact_Name",
        "Contact_Email",
        "Contact_Phone",
        "Notes",
    }
    if field not in allowed_fields:
        raise ValueError("Invalid field name provided.")

    query = f"SELECT {field} FROM tb_FSAR_Data_SampArtReq WHERE Request_ID = ?"
    cursor.execute(query, (job_etools_id,))

    return cursor


def _set_etools_field(job_etools_id, field, value):
    """
    A generic function to set a field to a value.

    Note:
    You do not want to fire these off in large numbers. If you need to update
    more than two or three fields at once, combine it into a single query!
    Each query creates a new connection and is therefore not something you
    want to do a lot.

    TODO: Add an optional argument to specify an existing connection/cursor.

    """
    cursor, connection = _get_conn_cursor()
    query = f"UPDATE tb_FSAR_Data_SampArtReq SET {field} = ? WHERE Request_ID = ?"
    cursor.execute(query, (value, job_etools_id))
    connection.commit()
    return cursor


def bool_to_yesno(bool_val):
    """Returns a 'Yes' or 'No' given a bool value."""
    if bool_val:
        return "Yes"
    else:
        return "No"


def _ensure_item_record_exists(cursor, connection, item):
    """
    If the specified item does not exist, create an empty entry to be updated.

    Returns True if the record already existed, or False if it had to be
    created.
    """
    # Check for existing item record
    cursor.execute(
        "SELECT TOP 1 * FROM tb_FSAR_Data_JobItem WHERE job_id = ? AND item_recid = ?",
        (item.job.id, item.num_in_job),
    )

    if not cursor.fetchone():
        # Create the missing item record
        cursor.execute(
            "INSERT INTO tb_FSAR_Data_JobItem (job_id, item_recid) VALUES (?, ?)",
            (item.job.id, item.num_in_job),
        )
        connection.commit()
        print("Item record for job %s item %s does not exist, creating." % (item.job.id, item.num_in_job))
        return False
    else:
        return True


def push_job(job):
    """Pushes a job back to etools."""
    cursor, connection = _get_conn_cursor()

    """
    >>> Begin query calculations <<<
    """
    try:
        assigned_to = job.artist.first_name[0] + job.artist.last_name[0]
    except AttributeError:
        assigned_to = "??"

    """
    >>> Begin assembling the query <<<
    """
    query_string = "UPDATE tb_FSAR_Data_SampArtReq SET " "Job_ID = ?, " "Job_Status = ?, " "Assigned_To = ? " "WHERE Request_ID = ?"
    cursor.execute(query_string, (job.id, job.status, assigned_to, job.e_tools_id))
    connection.commit()
    connection.commit()

    # Update the job's items as well.
    for item in job.item_set.all():
        push_item(cursor, connection, item)

    job.needs_etools_update = False
    job.save()


def push_item(cursor, connection, item):
    """
    Pushes an item record to eTools.

    NOTE: The original implementation contained many legacy SQL assembly
    paths and unbalanced/invalid syntax. Replace with a no-op stub that
    ensures the item record exists. Re-implement the full push logic when
    refactoring this module.
    """
    # Ensure the item record exists. If it doesn't, create it and commit.
    _ensure_item_record_exists(cursor, connection, item)
    return


def _populate_shipping(job, ejob):
    """
    Searches for existing address book entries, creates a new entry or returns
    an existing one based on the results.
    """
    # Wipe clean before re-loading if already in existence.
    JobAddress.objects.filter(job=job).delete()

    # Address 1
    if ejob.ship_name and ejob.ship_name != "n/a":
        ja = JobAddress()
        ja.job = job
        ja.name = ejob.ship_name or ""
        ja.address1 = ejob.ship_address1 or ""
        ja.address2 = ejob.ship_address2 or ""
        ja.city = ejob.ship_city or ""
        ja.country = ejob.ship_country or ""
        ja.company = ejob.ship_company or ""
        ja.phone = ejob.ship_phone or ""
        ja.state = ejob.ship_state or ""
        ja.zip = ejob.ship_zip or ""
        ja.save()

    # Address 2
    if ejob.fedex2name and ejob.fedex2name != "n/a":
        ja2 = JobAddress()
        ja2.job = job
        ja2.name = ejob.fedex2name or ""
        ja2.address1 = ejob.fedex2address or ""
        ja2.address2 = ejob.fedex2address2 or ""
        ja2.city = ejob.fedex2city or ""
        ja2.country = ejob.fedex2country or ""
        ja2.company = ejob.fedex2company or ""
        ja2.phone = ejob.fedex2phone or ""
        ja2.state = ejob.fedex2state or ""
        ja2.zip = ejob.fedex2zip or ""
        ja2.save()

    if ejob.fedex3name and ejob.fedex3name != "n/a":
        ja3 = JobAddress()
        ja3.job = job
        ja3.name = ejob.fedex3name or ""
        ja3.address1 = ejob.fedex3address or ""
        ja3.address3 = ejob.fedex3address2 or ""
        ja3.city = ejob.fedex3city or ""
        ja3.country = ejob.fedex3country or ""
        ja3.company = ejob.fedex3company or ""
        ja3.phone = ejob.fedex3phone or ""
        ja3.state = ejob.fedex3state or ""
        ja3.zip = ejob.fedex3zip or ""
        ja3.save()


def _determine_item_count(ejob):
    """
    Check the ejob attribute's graphic_qualityX attributes (where X is a
    number 1-9), and see if there is anything in them. Any graphic_qualityX
    variable that has a non-None value signifies that item X exists, and thus
    is counted.
    """
    # Counter
    num_items = 0

    # Silly eTools has hard-coded fields rather than a related table, limiting
    # us to 9 items and making things like determine item counts silly.
    for item_num in range(1, ETOOLS_MAX_ITEMS + 1):
        last_item = getattr(ejob, "graphic_quality%d" % item_num, None)

        if last_item and last_item.strip() != "":
            # Encountered a valid item, increment item count.
            num_items = item_num

            # Have to stop here or a None will result, since there will not
            # be another iteration if this is item 9.
            if item_num == ETOOLS_MAX_ITEMS:
                return item_num
        else:
            # No quality data, there are no more items to count.
            if DEBUG:
                print("ITEM COUNT:::", num_items)
            return num_items


def _create_missing_itemcatalog(size_mfg_name):
    """
    When a new/missing item size is requested, it needs to be added
    automatically. Add it and guess some of the values.
    """
    newsize = ItemCatalog()
    newsize.size = size_mfg_name
    newsize.mfg_name = size_mfg_name
    newsize.workflow = WORKFLOW

    """
    Attempt to guess the correct substrate based on the first character
    of the name.
    """
    size_firstchar = size_mfg_name[0]
    if size_firstchar == "S":
        newsize.product_substrate = app_defs.PROD_SUBSTRATE_SINGLE_POLY
    elif size_firstchar == "D":
        newsize.product_substrate = app_defs.PROD_SUBSTRATE_DOUBLE_POLY
    elif size_firstchar == "P":
        newsize.product_substrate = app_defs.PROD_SUBSTRATE_CLEAR_PLASTIC
    else:
        newsize.product_substrate = app_defs.PROD_SUBSTRATE_NOT_APPLICABLE

    newsize.save()
    return newsize


def _send_item_replaces_email(items_replacing_designs, job):
    """Sends an email to certain people when a new item replaces a previous design."""
    if items_replacing_designs:
        mail_subject = "Design Replaced: %s" % job
        mail_body = loader.get_template("emails/etools_replaces_design.txt")
        mail_context = {"items": items_replacing_designs, "job": job}
        mail_send_to = []
        mail_send_to.append(settings.EMAIL_GCHUB)
        group_members = User.objects.filter(groups__name="EmailGCHubNewItems", is_active=True)
        for user in group_members:
            mail_send_to.append(user.email)
        general_funcs.send_info_mail(mail_subject, mail_body.render(mail_context), mail_send_to)


def _populate_items(job, ejob):
    """Creates and associated the Item objects."""
    item_count = _determine_item_count(ejob)
    items_replacing_designs = []
    for item_num in range(1, item_count + 1):
        print("ITEM #", item_num)
        item = Item()
        item.job = job
        item.workflow = WORKFLOW

        """
        Do an ItemCatalog search based on mfg_name compared to the really
        janky size name in eTools. If there's a match, use that size. If there
        is none to be found, create one and try to guess some sensible defaults.
        Notify the user that a new size has been added.
        """
        size_mfg_name = getattr(ejob, "itemtype%d" % item_num)
        try:
            item.size = ItemCatalog.objects.get(mfg_name__iexact=size_mfg_name)
        except ItemCatalog.DoesNotExist:
            # No size match found, create a new one.
            newsize = _create_missing_itemcatalog(size_mfg_name)
            item.size = newsize

            # Tell the user to check the guessed details over. Create a
            # clickable link in the joblog that will take them to the edit
            # page for the item catalog.
            newsize_edit_url = reverse("itemcatalog_edit", args=[newsize.id])
            newsize_link = "<a href='%s' target='_blank'>%s</a>" % (
                newsize_edit_url,
                newsize.size,
            )
            item.job.do_create_joblog_entry(
                joblog_defs.JOBLOG_TYPE_CRITICAL,
                (
                    "A new size, %s, has been added to the specs database. "
                    "Please edit the entry and make sure the name and type are correct."
                )
                % newsize_link,
            )

        item.floor_stock = ejob.floorstock
        if ejob.replaces_previous_design_name:
            item.replaces = ejob.replaces_previous_design_name
        item.case_pack = getattr(ejob, "casepack_proof%d" % item_num)
        item.annual_use = getattr(ejob, "annualuse_proof%d" % item_num)
        # Number of colors
        item.num_colors_req = getattr(ejob, "color_item%d" % item_num)
        try:
            item.quality = getattr(ejob, "graphic_quality%d" % item_num)
        except Exception:
            item.quality = "B"
        wrappable_proof = getattr(ejob, "wrapproof%d" % item_num)
        # ETools is prone to having some junk data, so protect against that a bit.
        if wrappable_proof in (True, 1, "1", "True", "Yes", "yes"):
            item.wrappable_proof = True
        else:
            item.wrappable_proof = False
        item.save()
        item.create_folder()

        try:
            replace_bool = str(ejob.replaces_previous_design).strip()
            # Normalize string and compare, since ETools doesn't cleanse their data.
            if replace_bool.lower() in ("1", "true", "yes") or item.replaces.strip() != "":
                # if item.replaces.strip() != '':
                # This item replaces a design.
                items_replacing_designs.append(item)
        except AttributeError:
            # Null/None value, not replacing anything.
            pass

    # Send item replacement notification email (if applicable).
    _send_item_replaces_email(items_replacing_designs, job)


def _determine_art_rec_type(ejob):
    """
    Determines the correct value for the item's art_rec_type based on eTool's
    string output. Lookups are based off of the stuff in app_defs.py.
    """
    if ejob.arttype:
        type_text = ejob.arttype.upper()
    else:
        return None

    if "E-MAIL" in type_text:
        return app_defs.ART_REC_TYPE_DIGITAL_EMAIL
    elif "ORIGINAL" in type_text:
        return app_defs.ART_REC_TYPE_ORIGINAL_ART
    elif "CLEMSON" in type_text:
        return app_defs.ART_REC_TYPE_CLEMSON_CREATE
    elif "RECREATE" in type_text:
        return app_defs.ART_REC_TYPE_RECREATE_PRINT
    elif "ISDN" in type_text:
        return app_defs.ART_REC_TYPE_ISDN_FTP
    elif "DISK" in type_text:
        return app_defs.ART_REC_TYPE_DIGITAL_DISK
    else:
        return app_defs.ART_REC_TYPE_OTHER


def _populate_joblog(job, ejob):
    """Create minimal joblog entries for an imported eTools job.

    Keep this small and defensive: if joblog creation fails, swallow the
    exception so the import process can continue. This mirrors the
    conservative approach used by other _populate_* helpers in this
    module.
    """
    try:
        parts = []
        req = getattr(ejob, "Request_ID", None)
        if req:
            parts.append(f"eTools Request ID: {req}")
        cust = getattr(ejob, "Customer_Name", None)
        if cust:
            parts.append(f"Customer: {cust}")
        proj = getattr(ejob, "Project_Description", None)
        if proj:
            # Keep description reasonably short in the log entry
            parts.append(f"Description: {str(proj)[:200]}")

        if parts:
            job.do_create_joblog_entry(joblog_defs.JOBLOG_TYPE_JOB_CREATED, " | ".join(parts))
    except Exception:
        # Intentionally ignore joblog failures during import to avoid
        # failing the whole import process for non-critical logging issues.
        pass


def _lookup_user_email(user_email):
    """Looks for a User object with the specified email."""
    if user_email:
        return User.objects.get(email__iexact=user_email)
    return None


def encode_cursor_fields(cursor, ejob):
    """
    Re-encodes all of the data to UTF8 to prevent problems when saving to
    Postgres.
    """
    # Go through the list of columns
    for column in cursor.description:
        # If the column is a string, re-encode it to UTF8.
        if column[1] is str:
            # Get a reference to the attribute on the ejob
            attr = getattr(ejob, column[0], None)
            if attr:
                # Re-encode to UTF-8. If an unknown character is found, it
                # gets replaced with a placeholder.
                try:
                    u_attr = str(attr, "iso-8859-1")
                except Exception:
                    u_attr = attr
                # Use UTF-8 encoding to avoid mangling non-ASCII data
                attr = u_attr.encode("utf-8", "replace")


def import_new_jobs():
    """Imports new jobs whose status is 'new' in etools."""
    cursor = _get_new_jobs()
    for ejob in cursor:
        duplicates = Job.objects.filter(e_tools_id=str(ejob.Request_ID))
        if duplicates:
            # This prevents errors from repeatedly importing the job.
            print("Duplicate ETools ID found for %s, skipping." % (ejob.Request_ID))
            continue

        # Re-encode all field values to UTF8 to make sure no really bogus
        # characters are in the data.
        encode_cursor_fields(cursor, ejob)

        # Start Job object population
        job = Job()
        job.name = fs_api.strip_for_valid_filename(ejob.job_name)
        job.workflow = WORKFLOW
        job.due_date = ejob.dateneeded
        if ejob.shiptostate:
            job.ship_to_state = ejob.shiptostate
        job.art_rec_type = _determine_art_rec_type(ejob)
        # Contact stuff
        job.customer_name = ejob.contact_name
        if ejob.contact_email:
            job.customer_email = ejob.contact_email
        job.e_tools_id = ejob.Request_ID
        # New fields as of 3/12/08
        try:
            job.keep_upc = ejob.keep_same_UPC
            job.plantpress_change = ejob.Plant_Press_Change
            job.anticipated_plant = ejob.Anticipating_Manufacturing_Plant
        except Exception:
            pass
        # Try to match the print group from etools with one imported from QAD.
        try:
            job.printgroup, created = QAD_PrintGroups.objects.get_or_create(name=ejob.printgroup)
        except Exception:
            pass
        # Search for salesperson by email address. Email someone in IT if not
        # found -- in case new user needs to be created. Use lookup user in
        # import functions?
        try:
            print("Salesperson lookup")
            job.salesperson = _lookup_user_email(str(ejob.sales_email))
        except User.DoesNotExist:
            pass
        print(ejob.Request_ID)
        job.save()
        job.create_folder()
        print("Saved eTools request id #%d as job #%d." % (ejob.Request_ID, job.id))
        print("Beginning populations.")
        _populate_shipping(job, ejob)
        _populate_items(job, ejob)
        _populate_joblog(job, ejob)
        _set_etools_job_status(ejob.Request_ID, "Active")
        _set_etools_field(ejob.Request_ID, "Job_ID", job.id)
