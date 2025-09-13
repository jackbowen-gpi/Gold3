"""QAD/Datawarehouse operations module."""

import pyodbc
from django.conf import settings

# from django.urls import reverse
from gchub_db.apps.qad_data.models import QAD_CasePacks, QAD_PrintGroups


# Mock cursor class for development when QAD is disabled
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


DEBUG = False


def _get_conn_cursor():
    """
    In pyodbc, all SQL operations happen through the cursor. Get connected
    and return the cursor for use in a query.
    """
    # Check if QAD is disabled for development
    if not getattr(settings, "QAD_ENABLED", True):
        return MockCursor(), None

    connection = pyodbc.connect(settings.QAD_ODBC_DSN, ansi=True)
    return connection.cursor(), connection


def get_server_version():
    """Queries for the server's version info."""
    # Check if QAD is disabled for development
    if not getattr(settings, "QAD_ENABLED", True):
        return "Mock QAD SQL Server 2019 - Development Environment"

    cursor = _get_conn_cursor()[0]
    cursor.execute(
        "SELECT 'SQL Server ' + CONVERT(varchar(100),SERVERPROPERTY('productversion')) + "
        "' - ' + CONVERT(varchar(100),SERVERPROPERTY('productlevel')) + "
        "' - ' + CONVERT(varchar(100),SERVERPROPERTY('edition'))"
    )
    return cursor.fetchone()[0]


def _get_new_records():
    """
    Query for retrieving new records. Returns a cursor object, from which you
    may iterate through.
    """
    cursor = _get_conn_cursor()[0]
    cursor.execute("SELECT * FROM dbo.PrintGroups")

    if DEBUG:
        # Show a list of columns + their data types.
        for column in cursor.description:
            print(column)

    return cursor


def get_nine_digit_data(nine_digit):
    """Return data for the given nine-digit number from QAD>"""
    cursor = _get_conn_cursor()[0]
    cursor.execute("SELECT UPC, SCC FROM ProductSpecs where Part=?", (str(nine_digit),))

    if DEBUG:
        # Show a list of columns + their data types.
        for column in cursor.description:
            print(column)

    for col in cursor:
        encode_cursor_fields(cursor, col)
        upc = col.UPC
        scc = col.SCC

    return upc, scc


def get_specsheet_description(nine_digit):
    """
    Return the spec sheet description for the given nine-digit number from QAD.
    The description is made up of three lines stored across multiple tables.
    """
    # Collect the three lines in a list of strings.
    description_list = []

    try:
        cursor = _get_conn_cursor()[0]

        # Lines 1 and 2
        cursor.execute("SELECT Description, Description2 FROM ProductSpecs where Part='%s'" % str(nine_digit))
        data_first_attmpt = cursor.fetchone()
        description_list.append(data_first_attmpt[0])
        description_list.append(data_first_attmpt[1])

        # Line 3
        cursor.execute("SELECT cd_cmmt##1 FROM cd_det WHERE cd_ref = '%s'" % str(nine_digit))
        data_second_attmpt = cursor.fetchone()
        description_list.append(data_second_attmpt[0])

    except Exception:
        description_list.append("*QAD Error: End of data.*")

    return description_list


def get_email_data(nine_digit):
    """
    Returns some additional data that sales would like included in their nine
    digit notification email.
    """
    # Check if QAD is disabled for development
    if not getattr(settings, "QAD_ENABLED", True):
        # Return mock data for development
        return (
            12,  # casepack
            24,  # sleevecount
            15.5,  # weight
            "4 x 3",  # tihi (tier x high)
            0.85,  # cube
            "12.50",  # length
            "8.25",  # width
            "6.75",  # height
        )

    # Gonna define these variables with an error message first. If they don't
    # get over-written with data from QAD the error message will be what gets
    # returned.
    casepack = "Art Request Error: No case pack found."
    sleevecount = "QAD Error: No data found."
    weight = "QAD Error: No data found."
    tihi = "QAD Error: No data found."
    cube = "QAD Error: No data found."
    length = "QAD Error: No data found."
    width = "QAD Error: No data found."
    height = "QAD Error: No data found."

    # Grab the item based on the nine digit
    from gchub_db.apps.workflow.models import Item

    # If there are intermixed designes there could be multiple items with the
    # same nine digit. For this particular use they will be identical so just
    # use the first one.
    item = Item.objects.filter(fsb_nine_digit__contains=nine_digit)[0]

    # Read the data from QAD.
    cursor = _get_conn_cursor()[0]
    cursor.execute(
        """
                    SELECT xxstd__inner_pack sleevecount, xxstd__ship_wt weight,
                    xxstd__csly layer, xxstd__cspl pallet, xxstd__size cube,
                    xxstd__length length, xxstd__width width,
                    xxstd__height height
                    FROM xxpt_std
                    WHERE xxstd__part_type = '%s'
                    AND xxstd__case_pack = '%s'
                    """
        % (str(item.size.mfg_name), str(item.case_pack))
    )
    data = cursor.fetchone()

    # Attempt to assign the data to variables and return them
    if data:
        casepack = int(item.case_pack)
        sleevecount = int(data.sleevecount)
        weight = data.weight
        pallet = data.pallet
        layer = data.layer
        if pallet > 0 and layer > 0:
            tihi = "%s x %s" % (int(layer), int(pallet / layer))
        cube = data.cube
        length = "%.2f" % data.length
        width = "%.2f" % data.width
        height = "%.2f" % data.height

    return casepack, sleevecount, weight, tihi, cube, length, width, height


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
                attr = attr.encode("utf_8", "replace")


def import_new_records():
    """Imports new jobs whose status is 'new' in etools."""
    cursor = _get_new_records()

    # Clear the original table first.
    print("Updating QAD_PrintGroups data.")
    # QAD_PrintGroups.objects.all().delete()

    for ejob in cursor:
        # Re-encode all field values to UTF8 to make sure no really bogus
        # characters are in the data.
        encode_cursor_fields(cursor, ejob)

        # Start object population
        record, created = QAD_PrintGroups.objects.get_or_create(name=ejob.PrintGroup)
        record.description = ejob.PrintGrpName

        record.save()

        if DEBUG:
            print("Saved PrintGroup: %s." % ejob.PrintGroup)


def update_casepacks():
    """
    Checks QAD casepacks and updates GOLD casepacks accordingly. Does not yet
    check for removed casepacks.
    """
    print("Updating QAD Casepacks.")
    from gchub_db.apps.workflow.models.general import ItemCatalog

    # Get the current list of casepacks from QAD.
    cursor = _get_conn_cursor()[0]

    #    cursor.execute("""
    #                    SELECT pt_part_type, xxpt__case_pk
    #                    FROM pt_mstr_all
    #                    WHERE pt_domain = '037'
    #                    AND len(pt_part) = 9
    #                    GROUP BY pt_part_type, xxpt__case_pk
    #                    """)

    cursor.execute(
        """
                    SELECT xxstd__part_type, xxstd__case_pack
                    FROM xxpt_std
                    WHERE xxstd__domain = '037'
                    GROUP BY xxstd__part_type, xxstd__case_pack
                    """
    )

    data = cursor.fetchall()

    # Add new casepacks to GOLD.
    for row in data:
        #        print "%s: %s" %(row[0], row[1])
        try:  # See if we have this size
            size = ItemCatalog.objects.get(mfg_name=row[0])
            if size:
                try:
                    # this requires the check failing if there are none to create one in the exception
                    # so get the first result and if there are none if will fail, and if there 1 or more
                    # it wont create one
                    QAD_CasePacks.objects.filter(size=size, case_pack=row[1])[0]

                except IndexError:  # If we don't have it make it.
                    casepack = QAD_CasePacks()
                    casepack.size = size
                    casepack.case_pack = row[1]
                    casepack.save()
        except ItemCatalog.DoesNotExist:
            # No matching item size in GOLD for this QAD row; skip.
            continue

    """
    Select all casepacks from the active view and go through gold and see what we need to deactivated or activated
    """
    cursor.execute("""SELECT parttype, casepack from ActivePartTypeCSPK""")

    # this is our list of all active casepacks in QAD courtesy of Joe Hammond
    active_casepacks = cursor.fetchall()
    # This is our list of all casepacks that gold has a record of
    all_casepacks = QAD_CasePacks.objects.all()

    # this check is to make sure we get something from the QAD query, 20 was chosen as we felt just checking is
    # there was one or two might be an error we wanted to catch
    if len(active_casepacks) > 20:
        # iterate over the active_casepacks and check them against all_casepacks to see what we should activate in GOLD
        for row in active_casepacks:
            # get the specific casepack we are looking at from the active casepack list
            case_pack = all_casepacks.filter(size__mfg_name=row[0], case_pack=row[1])
            # if that case pack is in gold then we activate it.
            if case_pack:
                # This will check if we have the case pack AND if it is active, so set it to active and save
                case_pack[0].active = True
                case_pack[0].save()
                # remove this case pack from our total gold list and all that will be leftover is a list of casepacks
                # that are on the deactivate list.
                all_casepacks = all_casepacks.exclude(id=case_pack[0].id)

        # when we are finished, all_casepacks is now a list of case packs to deactivate
        for leftover_pack in all_casepacks:
            leftover_pack.active = False
            leftover_pack.save()
