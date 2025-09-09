"""Reads in ink coverage XMLs from backstage."""

import urllib
from xml.dom import minidom

from colormath.color_objects import sRGBColor

from gchub_db.apps.color_mgt.models import ColorDefinition
from gchub_db.apps.joblog import app_defs as joblog_defs
from gchub_db.apps.workflow.models import ColorWarning, ItemColor


class InkCoverageException(Exception):
    """Generic un-recoverable ink coverage problem."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    def __str__(self):
        return self.__unicode__()


class InkNode(object):
    """Abstraction for INK nodes in the XML document."""

    def __init__(self, ink_node):
        self.ink_node = ink_node
        self.ink_name = self.determine_ink_db_name()
        self.ink_angle = float(
            self.ink_node.getElementsByTagName("egInk:angle")[0].firstChild.nodeValue
        )
        self.rgb_r = float(
            self.ink_node.getElementsByTagName("egInk:r")[0].firstChild.nodeValue
        )
        self.rgb_g = float(
            self.ink_node.getElementsByTagName("egInk:g")[0].firstChild.nodeValue
        )
        self.rgb_b = float(
            self.ink_node.getElementsByTagName("egInk:b")[0].firstChild.nodeValue
        )
        self.ink_lpi = float(
            self.ink_node.getElementsByTagName("egInk:frequency")[
                0
            ].firstChild.nodeValue
        )

    def __str__(self):
        return self.ink_name

    def get_coverage_percentage(self):
        """Abstract this here, since it sometimes throws an IndexError if the
        node is without coverage data.
        """
        return float(
            self.ink_node.getElementsByTagName("egInkCov:pct")[0].firstChild.nodeValue
        )

    def get_coverage_sq_inch(self):
        """Abstract this here, since it sometimes throws an IndexError if the
        node is without coverage data.
        """
        # .00155 Converts from inches to mm
        return (
            float(
                self.ink_node.getElementsByTagName("egInkCov:mm2")[
                    0
                ].firstChild.nodeValue
            )
            * 0.00155
        )

    def get_color_hex_value(self):
        """Get the RGB values and spit out some hex."""
        srgb = sRGBColor(float(self.rgb_r), float(self.rgb_g), float(self.rgb_b), False)
        return srgb.get_rgb_hex()

    def is_importable_ink(self):
        """Makes sure this ink node is importable (Not a Die or Technical ink)."""
        # Lowered for matching purposes
        ink_name = self.ink_name.lower()

        # Both workflows ignore template and die inks.
        if ink_name in ["template", "die", "disc"] or "template" in ink_name:
            print("#> Template/die ink found, ignoring: %s" % ink_name)
            return False

        # Looks good, this node is fine to import.
        return True

    def determine_ink_db_name(self):
        """Given an ink_node, determine the ink's name as per the database. For
        example, GCH 123 or Warm Red.
        """
        ink_book = self.ink_node.getElementsByTagName("egInk:book")[
            0
        ].firstChild.nodeValue
        ink_name = self.ink_node.getElementsByTagName("egInk:name")[
            0
        ].firstChild.nodeValue

        if "ppasc" in ink_book:
            temp_ink_name = ink_name.split(" ")
            # The name should be something like Pantone 2345 C and we only want the number, so first
            # make sure there are three things returned in the array split and then only get the number
            # and return that. Pantone and Coating will be done later
            if len(temp_ink_name) == 3:
                ink_name = temp_ink_name[1]
            else:
                raise InkCoverageException(
                    "Proper ink name could not be determined for %s in the inkbook: %s. Ink coverage failed."
                    % (ink_name, ink_book)
                )

        try:
            # Sometimes ink that aren't in the ink book won't have a TYPE
            # attribute.
            ink_type = self.ink_node.getElementsByTagName("egInk:type")[
                0
            ].firstChild.nodeValue
        except KeyError:
            # In these cases, it's unknown whether we're dealing with a
            # process color. 99% of the times, this will not be a process
            # color. Give the ink type a value accordingly.
            ink_type = "UNK"

        if "process" in ink_type:
            # This is a process color.
            name_prefix = "Process "
        else:
            # Not a process color.
            name_prefix = ""

        return "%s%s" % (name_prefix, ink_name)

    def lookup_itemcolor(self, item):
        """Searches for an itemcolor by name. If it doesn't exist return None.

        item: (Item) The item that's being manipulated.
        """
        workflow_name = item.job.workflow.name

        try:
            """
            Beverage and carton items work the same here, error if the itemcolor is not already in GOLD
            """
            if workflow_name == "Foodservice":
                return ItemColor.objects.get(
                    item=item, color__iexact=self.ink_name, angle=str(self.ink_angle)
                )
            elif workflow_name == "Beverage":
                return ItemColor.objects.get(item=item, color__iexact=self.ink_name)
            else:
                # This should be just carton items at this point.
                ink_type = self.ink_node.getElementsByTagName("egInk:type")[
                    0
                ].firstChild.nodeValue
                # Need to capitalize the first color here to match how colors are in our system
                ink_name = self.ink_node.getElementsByTagName("egInk:name")[
                    0
                ].firstChild.nodeValue.capitalize()
                # Sometimes process black is used as a place-holder for low carbon black.
                if ink_type == "process" and ink_name == "Black":
                    try:  # Return the low carbon item color, if there is one.
                        return ItemColor.objects.get(
                            item=item, definition__name="Low-Carbon Black"
                        )
                    except Exception:  # No low carbon ink item color? Carry on.
                        pass
                # Process color logic
                if ink_type == "process" and ink_name in [
                    "Black",
                    "Cyan",
                    "Magenta",
                    "Yellow",
                ]:
                    colorDict = {
                        "Process Black": "90985234",
                        "Process Cyan": "90985253",
                        "Process Magenta": "90984629",
                        "Process Yellow": "90985250",
                    }
                    return ItemColor.objects.get(
                        item=item,
                        color__iexact=colorDict["Process %s" % (ink_name)],
                        definition__name="Process %s" % (ink_name),
                    )
                # Spot color logic
                else:
                    # Search by color first.
                    try:
                        return ItemColor.objects.get(
                            item=item, color__iexact=self.ink_name
                        )
                    except Exception:
                        pass
                    # Search by defintion if nothing was found by color.
                    return ItemColor.objects.get(
                        item=item, definition__name=self.ink_name
                    )

        except ItemColor.DoesNotExist:
            """
            Beverage and carton items kill the ink coverage if a match can't be found here.
            """
            if workflow_name == "Beverage" or workflow_name == "Carton":
                # Beverage does not create any new ItemColors, it merely matches
                # existing ones.
                print("-!> No ItemColor match found, ink coverage failed.")
                # Kill it here, this gets JobLogged as well.
                raise InkCoverageException(
                    "No match could be found for the ink named %s on item %d. Ink coverage failed."
                    % (self.ink_name, item.num_in_job)
                )
            else:
                """
                Foodservice just returns an empty ItemColor object.
                """
                # Foodservice creates and populates new ItemColors.
                ic = ItemColor()
                ic.item = item
                ic.color = self.ink_name
                return ic

        except Exception as ex:
            raise InkCoverageException("Error has occurred: %s." % str(ex)) from ex


class InkCoverageDocument(object):
    """Class for parsing and importing ink coverage XML documents."""

    # Head of the XML structure
    jdoc = None
    # Shortcut reference to the document's first child
    doc_root = None
    # When false, print some debugging stuff
    debug = False
    # Full path to the XML file
    xml_file = None

    def __init__(self, xml_file_path, debug=False):
        """Arguments:
        * xml_file_path (String): Full path to the XML file to parse
        * debug (bool): When true, print debugging info

        """
        # Parse the XML file path string and return the XML node structure.
        self.jdoc = minidom.parse(xml_file_path)
        self.xml_file = xml_file_path
        print(self.xml_file)
        # Shortcut reference to the document's first child, where things
        # start getting interesting (bypassing the paf:INFO node).
        self.doc_root = self.jdoc.firstChild
        self.debug = debug

    def get_job_number(self):
        """Returns the job number based on the XML file's file name."""
        # Grab the file name out of the full path by taking everything after
        # the last forward slash.
        file_name = self.xml_file.split("/")[-1:]
        # Anything before the dash should be a job number.
        return file_name[0].split("-")[0]

    def get_item_number(self):
        """Returns the item number."""
        # Get everything after the dash, then split by the period character
        # and get the first thing in that list (the item's number)
        remove_space = self.xml_file.split(" ")[0]
        second_half = remove_space.split("-")[1]
        minus_extension = second_half.split(".")[0]
        minus_nojdf = minus_extension.split("_")[0]
        return minus_nojdf

    def get_pdf_path(self, windows_format=True):
        """Returns the path to the PDF file being manipulated.

        If windows_format is True, make the slashes forward slashes and
        pre-pend file://. If False, return the raw path (more UNIX-style).
        """
        jobRef = self.jdoc.getElementsByTagName("egPrF:DerivedFrom")[0]
        raw_path = jobRef.getElementsByTagName("stRef:instanceID")[
            0
        ].firstChild.nodeValue
        less_raw_path = str(urllib.parse.unquote(urllib.parse.unquote(str(raw_path))))
        if windows_format:
            new_path = less_raw_path.replace("\\", "/")
            new_path = "%s" % (new_path)
            return new_path
        else:
            return raw_path

    def _get_ink_nodes(self):
        """Returns a NodeList of ink nodes."""
        return self.jdoc.getElementsByTagName("egGr:inks")[0].getElementsByTagName(
            "rdf:li"
        )

    def get_ink_str_list(self):
        """Returns a list of the PDF's ink names in string format."""
        inks = []
        for node in self._get_ink_nodes():
            inks.append(node.getElementsByTagName("egInk:name")[0].firstChild.nodeValue)
        return inks

    def _round_dimension(self, dim_float):
        """Given a float template dimension, round it to the 3 places then use
        a string formatting function to lop off the funkyness at the end of
        the number that arises from fp math.

        Returns a string number for comparison.
        """
        rounded = round(dim_float, 3)
        return "%.3f" % rounded

    def compare_dimensions(self, item):
        """Looks up the ItemSpec for this item and compares the VSIZE and HSIZE
        tag values to expected values. This helps catch when a job is proofed
        out on the wrong template.

        Returns True when dimensions match, False otherwise.
        """
        vsize = (
            float(
                self.doc_rootjdoc.getElementsByTagName("egGr:vsize")[
                    0
                ].firstChild.nodeValue
            )
            * 0.0393701
        )  # Convert from mm to inch
        vsize = self._round_dimension(vsize)
        hsize = (
            float(
                self.doc_root.getElementsByTagName("egGr:hsize")[0].firstChild.nodeValue
            )
            * 0.0393701
        )  # Convert from mm to inch
        hsize = self._round_dimension(hsize)

        try:
            ispec = item.get_item_spec()
        except Exception:
            # This is probably a Beverage job. Die silently anyway.
            return (True, "No problem.")

        if not ispec.template_horizontal or not ispec.template_vertical:
            ispec.template_horizontal = hsize
            ispec.template_vertical = vsize
            ispec.save()
            return (True, "No problem.")
        else:
            template_horizontal = self._round_dimension(ispec.template_horizontal)
            template_vertical = self._round_dimension(ispec.template_vertical)

            if template_horizontal == hsize and template_vertical == vsize:
                return (True, "No problem.")
            else:
                error_msg = (
                    "An ink coverage was sent for item number %s (<a href='%s' target='_blank'>%s</a>), but its dimensions (%s x %s) did not match the values in our Item Specifications (%s x %s). Please correct the art or the Item Specification."
                    % (
                        item.num_in_job,
                        ispec.get_absolute_url(),
                        ispec.size.size,
                        template_horizontal,
                        template_vertical,
                        hsize,
                        vsize,
                    )
                )
                return (False, error_msg)

    def import_disclaimer(self, item):
        """Imports the disclaimer text (if there is any).

        item: (Item) The workflow Item object to import to.
        """
        jinfo_node = self.jdoc.getElementsByTagName("dc:description")
        if jinfo_node:
            jinfo_nodes = jinfo_node[0].getElementsByTagName("rdf:li")
            # If the tag can't be found, fail silently.
            if jinfo_nodes:
                jnode = jinfo_nodes[0]
                dtext = jnode.firstChild.nodeValue
                item.disclaimer_text = dtext
                print("@> Importing Disclaimer:", dtext)
            else:
                # This allows artists to delete disclaimers if they had previously
                # entered one they no longer want.
                item.disclaimer_text = None
        else:
            # This allows artists to delete disclaimers if they had previously
            # entered one they no longer want.
            item.disclaimer_text = None
        item.save()

    def import_itemcolors(self, job, item):
        """Imports all of the ink data into ItemColor objects."""
        workflow_name = job.workflow.name

        if workflow_name == "Foodservice":
            # Foodservice wipes all item colors clean and re-populates them.
            print("$> Foodservice job found, wiping existing ItemColors.")
            item.itemcolor_set.all().delete()

        allCovers = self.jdoc.getElementsByTagName("egInkCovL:coverage")[0]
        covers = allCovers.getElementsByTagName("rdf:li")

        # Filter out technical inks
        inkNodes = self._get_ink_nodes()
        for x in range(len(inkNodes)):
            newElement = self.jdoc.createElement("egInkCov:pct")
            newElementText = self.jdoc.createTextNode(
                covers[x].getElementsByTagName("egInkCov:pct")[0].firstChild.nodeValue
            )
            newElement.appendChild(newElementText)
            inkNodes[x].appendChild(newElement)

            newElement = self.jdoc.createElement("egInkCov:mm2")
            newElementText = self.jdoc.createTextNode(
                covers[x].getElementsByTagName("egInkCov:mm2")[0].firstChild.nodeValue
            )
            newElement.appendChild(newElementText)
            inkNodes[x].appendChild(newElement)

        ink_nodes = [InkNode(node) for node in inkNodes]
        ink_nodes = [node for node in ink_nodes if node.is_importable_ink()]

        # Count the number of ink nodes in the coverage and ItemColor DB objects
        ink_node_count = len(ink_nodes)
        itemcolor_count = item.itemcolor_set.all().count()

        # If the ink coverage node count for Beverage doesn't match the DB, fail.
        if (
            workflow_name == "Beverage" or workflow_name == "Carton"
        ) and ink_node_count != itemcolor_count:
            # This gets JobLogged, the ink coverage is aborted.
            raise InkCoverageException(
                "Mis-match in ink count between the ink coverage (%d) and the item in the database (%d). Ink coverage failed."
                % (ink_node_count, itemcolor_count)
            )

        is_first_node = True
        # Go through each of the inks listed in the ink coverage document and
        # import an ItemColor object associated to the job/item for each.
        total_error_message = ""
        exception = False
        count = 0
        for node in ink_nodes:
            # This creates an ItemColor object with the correct values filled.
            ic = self.populate_itemcolor(node, job, item)
            if ic:
                # ItemColor was populated in some manner, save it.
                ic.save()

                # Check for colors we cannot hit
                warnings = ColorWarning.objects.filter(definition=ic.definition)
                if warnings and workflow_name == "Foodservice":
                    warning = warnings[0]
                    # Press change jobs should not be caught by Color Warning
                    if not job.duplicated_from and warning.active:
                        # Certain plastic sizes should not get color warnings
                        excluded_sizes = ["pmrp", "pmrk", "ptrpc", "ptrpt", "ptrpw"]
                        exclude_flag = False
                        # Check this item against the excluded sizes.
                        for excluded_size in excluded_sizes:
                            if excluded_size in str(item.size.size).lower():
                                exclude_flag = True
                        # Go ahead if this isn't an excluded size.
                        if not exclude_flag:
                            count = count + 1
                            total_error_message += (
                                "%d) Color warning: cannot hit %s. Replace with %s. \n "
                                % (count, ic.color, warning.qpo_number)
                            )
                            exception = True

                if workflow_name == "Beverage" and ic.lpi > 85:
                    # Ink coverage fails if any inks are greater than 65 lpi.
                    print("-!> LPI greater than 65, failing.")
                    count = count + 1
                    total_error_message += (
                        "%d) LPI on the ink named %s on item %d is greater than 65. Ink coverage failed. \n"
                        % (count, ic.color, item.num_in_job)
                    )
                    exception = True

                if workflow_name == "Foodservice":
                    # Set a sequence number for Foodservice item colors based on
                    # the total number of colors for the item.
                    ic.sequence = item.itemcolor_set.all().count()
                    ic.save()
                    # This method will take into account sequence and FSB Nine Digit
                    # if it exists to generate the full plate code.
                    ic.calculate_plate_code()

        if exception:
            raise InkCoverageException(total_error_message)

        item.do_create_joblog_entry(
            joblog_defs.JOBLOG_TYPE_JDF,
            "Ink coverage for item %d completed." % (item.num_in_job),
        )

        if workflow_name == "Foodservice" and "nojdf" not in self.xml_file:
            # Fire off a JDF to print the proof.
            print("-J> Triggering Foodservice JDF proofing.")
            item.do_jdf_fsb_proof()

        if workflow_name == "Beverage" and "nojdf" not in self.xml_file:
            # Fire off a JDF to print the proof.
            print("-J> Triggering Beverage workflow.")
            item.do_jdf_bev_workflow()

    def populate_itemcolor(self, ink_node, job, item):
        """Populates and returns an ItemColor object that is ready to be saved.
        Returns an ItemColor object to be saved by import_itemcolors().
        """
        # Returns a 'C' or 'U' for coated/uncoated.
        coating = item.size.get_coating_type(return_abbrev=True)

        # Print a summary of everything found so far.
        print(
            "#> %s %s (%s)" % (ink_node.ink_name, coating, item.size.product_substrate)
        )

        # This must be found now to check against other colors.
        color_angle = ink_node.ink_angle

        # This will either return an existing ItemColor to repopulate, or
        # create a new one if none can be found (depending on the workflow).
        ic = ink_node.lookup_itemcolor(item)

        """
        Start populating/re-populating the ItemColor.
        """
        # Try to look up a color definition based on name. On failure,
        # set the definition to None.
        try:
            ic.definition = ColorDefinition.objects.get(
                name__iexact=ic.color, coating=coating
            )
        except ColorDefinition.DoesNotExist:
            # Foodservice colors don't need to match against library.
            print("-!> No matching color definition for: %s" % ic.color)

        ic.hexvalue = ink_node.get_color_hex_value()
        print("--> Hex Value:", ic.hexvalue)

        # Various values based on tag names.
        try:
            ic.coverage_perc = ink_node.get_coverage_percentage()
            print("--> Ink Cov %:", ic.coverage_perc)
            ic.coverage_sqin = ink_node.get_coverage_sq_inch()
            print("--> Ink Cov In^2:", ic.coverage_sqin)
        except IndexError:
            # Just leave these values as None. This only happens in extremely
            # rare cases (IE: two of the same inks but with different angles).
            pass
        ic.lpi = ink_node.ink_lpi
        print("--> LPI:", ic.lpi)
        ic.angle = color_angle
        print("--> Angle:", ic.angle)

        # This is returned instead of saved here directly so that import_itemcolors()
        # can decide what to do in the case of oddities.
        return ic
