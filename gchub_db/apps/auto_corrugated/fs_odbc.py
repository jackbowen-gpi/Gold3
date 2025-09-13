"""This module manages syncing our local list of corrugated specs to the corporate
listing.

UPDATE

It was decided that we no longer want QAD to auto-sync corrugated specs with
GOLD due to things like rounding errors in QAD. This functionality has been
disabled but left in GOLD just in case we need to dust it off again later.

"""

import pyodbc
from django.conf import settings

# While True, output verbose debugging info.
DEBUG = False
# While True, print a list of columns on each eTools job request.
PRINT_COLUMNS = True


def _get_conn_cursor():
    """In pyodbc, all SQL operations happen through the cursor. Get connected
    and return the cursor for use in a query.
    """
    connection = pyodbc.connect(settings.QAD_ODBC_DSN)
    return connection.cursor(), connection


"""
It was decided that we no longer want QAD to auto-sync corrugated specs with
GOLD due to things like rounding errors in QAD. This functionality has been
disabled but left in GOLD just in case we need to dust it off again later.
"""

# def _get_all_specs():
#     """
#     Query for retrieving new jobs. Returns a cursor object, from which you
#     may iterate through.
#     """
#     cursor = _get_conn_cursor()[0]
# #     cursor.execute("SELECT DISTINCT PartType, CasePack, SleeveCount, Length, Width, "
#                    "Height from ProductSpecs WHERE Width != 'null' ORDER BY PartType")
#     # Joe Hammond suggested we use this newer view/statement which is quicker.
# #     cursor.execute("SELECT PartType, CasePack, Sleeve, Length, Width, Height "
#                    "FROM PartTypeStandards")
#     if PRINT_COLUMNS:
#         # Show a list of columns + their data types.
#         for column in cursor.description:
#             print column
#
#     return cursor

# def import_fsb_corrugated_specs():
#     """
#     Top-level importer function.
#     """
#     cursor = _get_all_specs()
#     for spec in cursor:
#         try:
#             if spec.PartType:
#                 item = ItemCatalog.objects.get(mfg_name__iexact=spec.PartType)
#             else:
#                 print "No part type:", spec
#                 continue
#         except ItemCatalog.DoesNotExist:
#             print "No ItemCatalog match:", spec.PartType
#             continue
#
#         try:
#             boxitem = BoxItem.objects.get(item_name=item.size)
#         except BoxItem.DoesNotExist:
#             print "No BoxItem match:", item
#             continue
#
#         try:
#             bs, created = BoxItemSpec.objects.get_or_create(boxitem=boxitem,
#                                                             case_count=spec.CasePack)
#             bs.sleeve_count = spec.Sleeve
#             bs.length = float(spec.Length)
#             bs.width = float(spec.Width)
#             bs.height = float(spec.Height)
#             bs.save()
#         except:
#             print "Error updating: %s %s" %(item, spec)
