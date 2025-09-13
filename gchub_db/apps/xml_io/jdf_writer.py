"""Generic JDF writer"""

import glob
import os
from xml.dom import minidom

from django.conf import settings
from django.utils import timezone


class ItemJDF(object):
    """JDF operations on workflow Items."""

    # Holds the minidom Document
    doc = None
    # Reference to the root containing JDF node
    doc_root = None
    # Reference to the workflow Item we're interacting with
    item = None

    def __init__(self, item, file_list, extra_vars=[]):
        """Document initialization."""
        self.doc = minidom.Document()
        self.item = item

        self.doc_root = self.doc.createElement("JDF")
        self.doc_root.setAttribute("DescriptiveName", "GOLD JDF Task")
        self.doc_root.setAttribute("ID", "n0001")
        self.doc_root.setAttribute("Status", "Waiting")
        self.doc_root.setAttribute("Type", "ProcessGroup")
        self.doc_root.setAttribute("Version", "1.2")
        self.doc_root.setAttribute("xmlns", "http://www.CIP4.org/JDFSchema_1_2")
        self.doc_root.setAttribute("xmlns:eg", "http://www.esko-graphics.com/EGschema1_0")
        self.doc.appendChild(self.doc_root)

        for key in file_list.keys():
            resource_pool = self.doc.createElement("ResourcePool")
            runlist_param = self.doc.createElement("RunList")
            runlist_param.setAttribute("Class", "Parameter")
            runlist_param.setAttribute("ID", key)
            runlist_param.setAttribute("PartIDKeys", "Run")
            runlist_param.setAttribute("Status", "Available")
            # runlist_param.setAttribute('DescriptiveName', '1-up')

            run_counter = 1
            for sfile in file_list[key]:
                runlist_run = self.doc.createElement("RunList")
                runlist_run.setAttribute("Run", "Run%04d" % run_counter)
                run_counter += 1

                layout_element = self.doc.createElement("LayoutElement")
                filespec = self.doc.createElement("FileSpec")
                filespec.setAttribute("URL", sfile)
                layout_element.appendChild(filespec)
                runlist_run.appendChild(layout_element)

                # Tabbing this line over 1/2011... was not in for loop before.
                runlist_param.appendChild(runlist_run)
        resource_pool.appendChild(runlist_param)

        if extra_vars:
            # Extra vars are additional ResourcePool parameters that serve
            # much like defining variables or allocating space for them ahead
            # of time.
            for var in extra_vars.keys():
                new_var = self.doc.createElement("RunList")
                new_var.setAttribute("Class", "Parameter")
                new_var.setAttribute("ID", var)

                sub_vars = extra_vars[var]
                if sub_vars:
                    for sub_var in sub_vars:
                        new_var.setAttribute(sub_var, sub_vars[sub_var])
                resource_pool.appendChild(new_var)

        self.doc_root.appendChild(resource_pool)

    def add_task_node(
        self,
        descriptive_name,
        node_id,
        task_id,
        ticket_name,
        task_output_id,
        priority=50,
        task_input_id="SourceFileList",
        task_status="Available",
        task_hold="false",
        smartmark_set=None,
    ):
        """
        Adds a generic, configurable task node to the document.

        descriptive_name: (str) Description of the document's purpose.
        node_id: (str) JDF task tag's ID.
        task_id: (str) Task's ID attribute.
        ticket_name: (str) Backstage ticket to use.
        task_output_id: (str) The ID of output resource pool (if any).
        """
        # Begin containing JDF tag
        new_node = self.doc.createElement("JDF")
        new_node.setAttribute("DescriptiveName", descriptive_name)
        new_node.setAttribute("ID", node_id)
        new_node.setAttribute("Status", "Waiting")
        new_node.setAttribute("Type", "eg:BackStageTask")
        new_node.setAttribute("Version", "1.2")
        new_node.setAttribute("xmlns", "http://www.CIP4.org/JDFSchema_1_1")
        new_node.setAttribute("xmlns:eg", "http://www.esko-graphics.com/EGschema1_0")

        # NodeInfo is by itself within JDF
        node_info = self.doc.createElement("NodeInfo")
        node_info.setAttribute("JobPriority", str(priority))
        new_node.appendChild(node_info)
        # End NodeInfo

        # ResourcePool contains BackStageTaskParams
        resource_pool = self.doc.createElement("ResourcePool")
        # Begin task params
        task_params = self.doc.createElement("eg:BackStageTaskParams")
        task_params.setAttribute("Class", "Parameter")
        task_params.setAttribute("ID", task_id)
        task_params.setAttribute("Status", task_status)
        task_params.setAttribute("eg:TicketName", ticket_name)
        task_params.setAttribute("eg:Hold", task_hold)

        # If a smartmark set is specified, include it in the backstage params.
        if smartmark_set:
            flex_params = self.doc.createElement("eg:FlexRipParam")
            flex_params.setAttribute("eg:MarkSet", smartmark_set)
            task_params.appendChild(flex_params)

        resource_pool.appendChild(task_params)
        # End task params
        new_node.appendChild(resource_pool)
        # End ResourcePool

        # ResourceLinkPool contains a few link related elements
        resource_link_pool = self.doc.createElement("ResourceLinkPool")

        # Begin Task Params Link
        task_params_link = self.doc.createElement("eg:BackStageTaskParamsLink")
        task_params_link.setAttribute("Usage", "Input")
        task_params_link.setAttribute("rRef", task_id)
        resource_link_pool.appendChild(task_params_link)
        # End Task Params Link

        # Input and output links
        input_link = self.doc.createElement("RunListLink")
        input_link.setAttribute("Usage", "Input")
        input_link.setAttribute("rRef", task_input_id)
        resource_link_pool.appendChild(input_link)

        output_link = self.doc.createElement("RunListLink")
        output_link.setAttribute("Usage", "Output")
        output_link.setAttribute("rRef", task_output_id)
        resource_link_pool.appendChild(output_link)
        # End input and output links

        new_node.appendChild(resource_link_pool)
        # End ResourceLinkPool

        self.doc_root.appendChild(new_node)

    def get_xml_doc_string(self, pretty=False):
        """Returns a string representation of the document via prettyprint."""
        if pretty:
            return self.doc.toprettyxml()
        else:
            return self.doc.toxml()

    def check_jdf_exists(self, file_name, jdf_queue_path):
        """
        Checks to see if a jdf file exists for that job already and throws a growl error
        so that two jobs dont get processed by automation engine at the same time.
        """
        try:
            fileNameArr = file_name.split("-")
            checkFileName = fileNameArr[0] + "-" + fileNameArr[1] + "*"
        except Exception:
            checkFileName = file_name

        """
        glob checks filenames and allows for wildcard searches (returning an array of matches)
        so that we can see if any jobs exist for an item/job.

        The filenames are checked when there are duplicated to make sure that different versions of the
        same item are still allowed
        """
        folderFilesToCheck = glob.glob(os.path.join(jdf_queue_path, checkFileName))
        if folderFilesToCheck:
            # function flag
            duplicateExists = False
            # for each file in the jdf automation engine folder
            for checkFile in folderFilesToCheck:
                # get the filename out of the absolute paths returned from glob
                pathsArr = checkFile.split("/")
                # the filename in the folder we are currently checking is the last spot in the path
                checkFileTemp = pathsArr[-1]
                # compare the filename to the file we want to write and see if it is the same name or not
                if file_name == checkFileTemp:
                    duplicateExists = True
            # if duplicates then return true and error else return false
            if duplicateExists:
                return True
            else:
                return False
        else:
            return False

    def send_jdf(self, file_name_override=None, jdf_path_override=None):
        """Creates the JDF file and drops it in the hotfolder."""
        if jdf_path_override is not None:
            jdf_queue_path = jdf_path_override
        else:
            jdf_queue_path = settings.JDF_ROOT

        if file_name_override is not None:
            file_name = file_name_override
        else:
            file_name = "%s-%s-%s.jdf" % (
                self.item.job.id,
                self.item.num_in_job,
                timezone.now().strftime("%d_%m-%H_%M_%S"),
            )

        if self.check_jdf_exists(file_name, jdf_queue_path):
            error_msg = (
                "Too many JDF tasks launched back-to-back on this item. "
                "Only the first task will run. You can launch another JDF task in 1 minute."
            )
            self.item.job.growl_at_artist(
                "JDF error on %s-%s %s" % (self.item.job.id, self.item.num_in_job, self.item.job.name),
                error_msg,
                pref_field="growl_hear_jdf_processes",
            )
        else:
            f = open(os.path.join(jdf_queue_path, file_name), "w")
            f.write(self.get_xml_doc_string())
            f.close()
