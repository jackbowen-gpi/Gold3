"""
This module contains EskoColor, which is used to abstract access to
colors within Kalleidescope color books.
"""

from configparser import RawConfigParser

from colormath.color_objects import SpectralColor


class InvalidColor(Exception):
    """Raised when the user asks for an color that does not exist."""

    def __init__(self, color_fullpath):
        self.path = color_fullpath

    def __str__(self):
        return "The specified color does not exist: %s" % self.path


class EskoColor(object):
    """
    Abstracts access to inkbook files that are located on the Esko bg_cms_data
    share. From here, you can get color values and perform some calculations.
    """

    def __init__(self, color_name, color_spec_res_path):
        """
        color_name: (str) Raw, user-provided color name that was queried for.
        color_spec_res_path: (str) Path to the color's *_ras_spec.res file.
        """
        self.name = color_name
        self.color_spec_res_path = color_spec_res_path

        try:
            self.fobj = open(self.color_spec_res_path, "r")
        except IOError:
            raise InvalidColor(self.color_spec_res_path) from None

        self.config_parser = RawConfigParser()
        self.config_parser.read_file(self.fobj)

    def __str__(self):
        return "EskoColor: %s" % self.name

    def get_spectral_color_obj(self):
        """Returns a python-colormath SpectralColor object for this color."""
        # These variables need to be pre-instantiated for the tuple splitting
        # to work further down.
        # v0 Options
        w380 = w390 = w400 = w410 = w420 = w430 = w440 = w450 = w460 = w470 = None
        # v1 Options
        w480 = w490 = w500 = w510 = w520 = w530 = w540 = w550 = w560 = w570 = None
        # v2 Options
        w580 = w590 = w600 = w610 = w620 = w630 = w640 = w650 = w660 = w670 = None
        # v3 Options
        w680 = w690 = w700 = w710 = w720 = w730 = None

        # Get each line of spectral float numbers and stuff them into variables
        # according to their [guessed] wavelength. Notice that the 'cow01000'
        # property is what we assume to be 'Color On White', as in the
        # substrate's white value.

        # Specify the name of the header that the color information will be found.
        color_header_name = self.name.replace(" ", "_") + "_100_w"

        # First line
        v0_values = self.config_parser.get(color_header_name, "v0").split()
        v0_float_list = [float(num) for num in v0_values]
        w380, w390, w400, w410, w420, w430, w440, w450, w460, w470 = tuple(v0_float_list)
        # Second line
        v1_values = self.config_parser.get(color_header_name, "v1").split()
        v1_float_list = [float(num) for num in v1_values]
        w480, w490, w500, w510, w520, w530, w540, w550, w560, w570 = tuple(v1_float_list)
        # Third line
        v2_values = self.config_parser.get(color_header_name, "v2").split()
        v2_float_list = [float(num) for num in v2_values]
        w580, w590, w600, w610, w620, w630, w640, w650, w660, w670 = tuple(v2_float_list)
        # Fourth line
        v3_values = self.config_parser.get(color_header_name, "v3").split()
        v3_float_list = [float(num) for num in v3_values]
        w680, w690, w700, w710, w720, w730 = tuple(v3_float_list)

        spc = SpectralColor(
            observer=2,
            illuminant="d50",
            spec_380nm=w380,
            spec_390nm=w390,
            spec_400nm=w400,
            spec_410nm=w410,
            spec_420nm=w420,
            spec_430nm=w430,
            spec_440nm=w440,
            spec_450nm=w450,
            spec_460nm=w460,
            spec_470nm=w470,
            spec_480nm=w480,
            spec_490nm=w490,
            spec_500nm=w500,
            spec_510nm=w510,
            spec_520nm=w520,
            spec_530nm=w530,
            spec_540nm=w540,
            spec_550nm=w550,
            spec_560nm=w560,
            spec_570nm=w570,
            spec_580nm=w580,
            spec_590nm=w590,
            spec_600nm=w600,
            spec_610nm=w610,
            spec_620nm=w620,
            spec_630nm=w630,
            spec_640nm=w640,
            spec_650nm=w650,
            spec_660nm=w660,
            spec_670nm=w670,
            spec_680nm=w680,
            spec_690nm=w690,
            spec_700nm=w700,
            spec_710nm=w710,
            spec_720nm=w720,
            spec_730nm=w730,
        )
        return spc

    def get_lab_color_obj(self):
        """Returns a python-colormath LabColor object."""
        spec = self.get_spectral_color_obj()
        return spec.convert_to("lab")
