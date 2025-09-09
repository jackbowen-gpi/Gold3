"""Module for reading Esko's proprietary colorbook files. This exposes almost all
of the color definitions in kalleidescope.
"""

import os
from configparser import RawConfigParser

from django.conf import settings

from .color_reader import EskoColor


class InvalidColorBook(Exception):
    """Raised when the user asks for an colorbook that does not exist."""

    def __init__(self, colorbook_fullpath):
        self.path = colorbook_fullpath

    def __str__(self):
        return "The specified color book does not exist: %s" % self.path


class EskoColorBook(object):
    """Abstracts access to Esko CMS ColorBook data. From this class, you can gain
    access to individual colors within colorbooks, along with its color data.
    """

    def __init__(self, colorbook_name):
        """Constructor.

        colorbook_name: (str) Name of the colorbook, as per Kalleidescope.
        """
        self.name = colorbook_name
        # Path to the colorbook's .res file.
        self.resfile_path = None
        # Path to the colorbook's cdb data directory.
        self.cdb_path = None

        self._calc_path_from_colorbook_name(colorbook_name)
        try:
            self.fobj = open(self.resfile_path, "r")
        except IOError:
            raise InvalidColorBook(self.resfile_path) from None

        self.config_parser = RawConfigParser()
        self.config_parser.readfp(self.fobj)

    def __str__(self):
        return "EskoColorBook: %s" % self.name

    def _calc_path_from_colorbook_name(self, colorbook_name):
        """Given an colorbook name, calculate the path.

        colorbook_name: (str) Name of the colorbook, as per Kalleidescope.
        """
        # No spaces are found in res files or cdb directory names.
        colorbook_name = colorbook_name.replace(" ", "_")
        # Calc the name of the .res file for the colorbook. This serves as
        # an index for the colorbook.
        colorbook_filename = "cb_%s_pos.res" % colorbook_name
        # Get the full path to the colorbook .res file.
        self.resfile_path = os.path.join(settings.ESKO_CMS_DATA_DIR, colorbook_filename)

        # Calc full path to the colorbook's cdb (Color DB?) directory. This
        # has all of the naughty bits.
        colorbook_cdb_dir = "%s_cdb" % colorbook_name
        # Get the full path to the cdb dir.
        self.cdb_path = os.path.join(settings.ESKO_CMS_DATA_DIR, colorbook_cdb_dir)

        # This is the res files that contains all the spectral data for
        # the colorbook.
        colorbook_specs_filename = "cdb_%s_spec.res" % colorbook_name.lower()
        # Monkeypatch! Stupid 31 char. filename limit...
        if colorbook_name == "FSB_Pantone_Uncoated":
            colorbook_specs_filename = "CDA6F9~1.RES"
        # Path to the spec file for the entire CDB.
        self.spec_file_path = os.path.join(self.cdb_path, colorbook_specs_filename)

    def get_color_name_list(self):
        """Return a list of string color names."""
        return self.config_parser.sections()

    def get_color(self, color_name):
        """Retrieves an EskoColorBookColor object for the specified color.

        color_name: (str) Raw color name as it appears in the Kalleidescope
                          color listing/colorbook.
        """
        parsed_name = color_name.replace(" ", "_")
        # color_filename = 'cdb_%s_ras_spec.res' % parsed_name
        # color_spec_res_path = os.path.join(self.cdb_path, color_filename)
        return EskoColor(color_name, self.spec_file_path)
