"""JDF readers."""

import os
from xml.dom import minidom


class JDFAuditPool(object):
    """A class for storing information from a JDF AuditPool."""

    def __init__(self, audit_pool_node):
        """
        Pass an AuditPool XML node to this constructor to parse and store the
        data in a more convenient format.
        """
        self.root_node = audit_pool_node
        # Stores the comments that have been smushed together from lists.
        self.comments = ""
        # The value of the ProcessRun's EndStatus attribute. Can be stuff like
        # 'Completed' or 'Aborted'
        self.end_status = None

        for child in audit_pool_node.childNodes:
            # Notification Comments are stored in the comments attribute on the
            # AuditPool object, and the overall end result is grabbed from
            # the ProcessRun element.
            if child.tagName == "Notification":
                # Cosmetic more than anything. Don't line break on first comment.
                if self.comments != "":
                    self.comments += "\n\r"
                self.comments += child.getElementsByTagName("Comment")[0].childNodes[0].data
            elif child.tagName == "ProcessRun":
                # This is the overall end result of this process.
                self.end_status = child.getAttribute("EndStatus")


class JDFTask(object):
    """Stores one of the JDF tag sections."""

    def __init__(self, jdf_task_node):
        """
        Pass a JDF XML node to this constructor to parse and store the
        data in a more convenient format.
        """
        # Reference to the JDF task node.
        self.root_node = jdf_task_node
        # Common attribute values.
        self.descriptive_name = jdf_task_node.getAttribute("DescriptiveName")
        self.id = jdf_task_node.getAttribute("ID")
        self.status = jdf_task_node.getAttribute("Status")
        self.type = jdf_task_node.getAttribute("Type")
        # Storage for AuditPool objects
        self.audit_pools = []
        # Populate the AuditPool list.
        self._store_auditpool_nodes()

    def _store_auditpool_nodes(self):
        """
        Store the AuditPool tags into JDFAuditPool objects and stuff them in
        the audit_pools list on this JDFTask object for easy retrieval.
        """
        audit_pools = self.root_node.getElementsByTagName("AuditPool")
        for pool in audit_pools:
            self.audit_pools.append(JDFAuditPool(pool))

    def return_comments(self):
        """Returns all of the comments from the AuditPool in this task."""
        for pool in self.audit_pools:
            return pool.comments


class JDFReader(object):
    """
    Reads a JDF that has been parsed and spat back out by Backstage. Looks
    for the presence of errors and other important things.
    """

    # This is set to True when the reader detects an aborted task.

    def __init__(self, jdf_file_path):
        """Initialize the JDFReader object and store some commonly needed values."""
        # If this is True, one of the JDFTask objects returned as Aborted
        # or Failed.
        self.has_aborted_tasks = False
        # Stored JDFTask element list. The first one is always the 'master'
        # JDF node that encapsulates all of the sub-tasks. It is best to think
        # of it as the summary.
        self.jdf_tasks = []

        # Store the JDF's file name for later usage.
        self.filename = jdf_file_path
        # Parse the XML doc, return the minidom document we need.
        self.doc = minidom.parse(jdf_file_path)
        # Calculate the job and item numbers based on the JDF's file name.
        self._calc_job_and_item_nums()
        # See if there were any Aborted processes.
        self._detect_aborted_processes()

        # This is really only necessary if we have aborted tasks. We're not
        # really interested in diagnostic information otherwise.
        if self.has_aborted_tasks:
            self._store_jdf_tasks()

    def _calc_job_and_item_nums(self):
        """
        Calculates the job number and the item's num_in_job based on the
        JDf filename.
        """
        # This lops off the path and just leaves the filename.
        filename = os.path.basename(self.filename)
        # Only interested in the job and item num from the file name.
        # The file is in the format of jobnum-itemnum-date.jdf
        split_name = filename.split("-")
        self.job_num = split_name[0]
        self.item_num_in_job = split_name[1]

    def _store_jdf_tasks(self):
        """
        Stores all of the JDF nodes in JDFTask objects and stuffs them in the
        self.jdf_tasks lists for easy later retrieval.
        """
        jdf_tasks = self.doc.getElementsByTagName("JDF")
        for jtask in jdf_tasks:
            self.jdf_tasks.append(JDFTask(jtask))

    def _detect_aborted_processes(self):
        """
        Look for ProcessRun tags with an EndStatus attribute containing
        'Aborted'. This lets us know something went wrong and further
        investigation is needed.
        """
        processes = self.doc.getElementsByTagName("ProcessRun")
        for process in processes:
            if process.getAttribute("EndStatus") == "Aborted":
                # Backstage was unable to finish the job for some reason.
                self.has_aborted_tasks = True
