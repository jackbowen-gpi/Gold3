"""This module holds generic Canvas classes with some minor extensions."""

from reportlab.lib import pdfencrypt
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas


class GenericCanvas(object):
    def __init__(self, file_name, width, height, encrypt=False, *args, **kwargs):
        self.element_list = []
        if encrypt:
            """
            If encrypted, set it on the main canvas so that the PDF cannot
            be edited, resaved, or printed. Should make it fairly difficult
            for them to use as production quality artwork.
            """
            enc = pdfencrypt.StandardEncryption("", canPrint=1, canModify=0, canCopy=0, canAnnotate=0)
            self.canvas = Canvas(file_name, pagesize=(width * inch, height * inch), encrypt=enc)
        else:
            self.canvas = Canvas(file_name, pagesize=(width * inch, height * inch))
