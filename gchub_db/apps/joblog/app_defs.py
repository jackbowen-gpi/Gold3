"""
Definitions that are specific to the joblog app. This file should never
include other files aside from base Django stuff.
"""

"""
Job-related entry types.
"""
# Job was created.
JOBLOG_TYPE_JOB_CREATED = 1
# Every time a job is saved.
JOBLOG_TYPE_JOB_SAVED = 2

"""
Item-related entry types.
"""
# Item added to job.
JOBLOG_TYPE_ITEM_ADDED = 3
# Item details updated.
JOBLOG_TYPE_ITEM_SAVED = 4
# Item was deleted from a job.
JOBLOG_TYPE_ITEM_DELETED = 5

"""
Workflow/production entry types.
"""
JOBLOG_TYPE_PRODUCTION_EDITED = 6
# General note/comment was added to the log.
JOBLOG_TYPE_NOTE = 7
# Something JDF-related happened.
JOBLOG_TYPE_JDF = 8
# Something bad JDF-related happened.
JOBLOG_TYPE_JDF_ERROR = 9
# ??
JOBLOG_TYPE_BILLING = 10
# Fedex labels were printed.
JOBLOG_TYPE_FEDEX = 11
# A joblog entry was removed.
JOBLOG_TYPE_JOBLOG_DELETED = 12

"""
Job/item status changes and events.
"""
# A revision was entered for an item.
JOBLOG_TYPE_ITEM_REVISION = 13
# Item is approved. This is critical for tracking approvals (customer signature) in the timeline.
JOBLOG_TYPE_ITEM_APPROVED = 14
# Item is filed out. This is critical for tracking file out (sent to platemaking) in the timeline.
JOBLOG_TYPE_ITEM_FILED_OUT = 15
# Item is proofed. This is critical for tracking proofs (sent to customer) in the timeline.
JOBLOG_TYPE_ITEM_PROOFED_OUT = 16
# Item has 9 digit number issued. This is critical for tracking in the timeline.
JOBLOG_TYPE_ITEM_9DIGIT = 17
# Item is approved. This is critical for tracking approvals in the timeline.
JOBLOG_TYPE_ITEM_REJECTED = 18
# Item is rejected.
JOBLOG_TYPE_ITEM_FORECAST = 25
# Item is forecasted.
JOBLOG_TYPE_ITEM_PREFLIGHT = 26
# Item is preflighted.

"""
General entry types.
"""
# For critical joblog entries, must show up on the front page to the user.
JOBLOG_TYPE_CRITICAL = 19
# An FTP action completed successfully.
JOBLOG_TYPE_FTP = 20
# A first-time QC was finalized.
JOBLOG_TYPE_QC_SUBMITTED = 23
# A review QC was finalized.
JOBLOG_TYPE_REVIEW_QC_SUBMITTED = 24

"""
Errors, messages, and bears, oh my!
"""
# Something bad has happened
JOBLOG_TYPE_ERROR = 21
# Something bad may have happened or might happen.
JOBLOG_TYPE_WARNING = 22

"""
Choices table for the JobLog model.
"""
JOBLOG_TYPES = (
    (JOBLOG_TYPE_JOB_CREATED, "Job Created"),
    (JOBLOG_TYPE_JOB_SAVED, "Job Saved"),
    (JOBLOG_TYPE_JOBLOG_DELETED, "Deleted Log"),
    (JOBLOG_TYPE_ITEM_SAVED, "Item Saved"),
    (JOBLOG_TYPE_ITEM_ADDED, "Item Added"),
    (JOBLOG_TYPE_ITEM_DELETED, "Item Deleted"),
    (JOBLOG_TYPE_ITEM_APPROVED, "Approved"),
    (JOBLOG_TYPE_ITEM_FILED_OUT, "Filed Out"),
    (JOBLOG_TYPE_ITEM_PROOFED_OUT, "Proofed"),
    (JOBLOG_TYPE_ITEM_9DIGIT, "Nine Digit Added"),
    (JOBLOG_TYPE_ITEM_FORECAST, "Item Forecast"),
    (JOBLOG_TYPE_ITEM_PREFLIGHT, "Item Preflight"),
    (JOBLOG_TYPE_ITEM_REJECTED, "Item Rejected"),
    (JOBLOG_TYPE_PRODUCTION_EDITED, "Production Edited"),
    (JOBLOG_TYPE_ITEM_REVISION, "Revision"),
    (JOBLOG_TYPE_BILLING, "Billing"),
    (JOBLOG_TYPE_NOTE, "Note"),
    (JOBLOG_TYPE_JDF, "JDF Action"),
    (JOBLOG_TYPE_JDF_ERROR, "JDF Error"),
    (JOBLOG_TYPE_FEDEX, "Fedex"),
    (JOBLOG_TYPE_CRITICAL, "Critical Info"),
    (JOBLOG_TYPE_FTP, "FTP Action"),
    (JOBLOG_TYPE_WARNING, "Warning"),
    (JOBLOG_TYPE_ERROR, "Error"),
    (JOBLOG_TYPE_QC_SUBMITTED, "QC Submitted"),
    (JOBLOG_TYPE_REVIEW_QC_SUBMITTED, "Review QC Submitted"),
)
