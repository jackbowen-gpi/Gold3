from django.http import HttpResponse

from .gold_json import JSMessage


class JSONErrorForm(object):
    """
    This class is meant to be used in conjunction with a Django form. It
    serializes any error messages and presents them in a unified way to the
    user via the JSMessage class.
    """

    def serialize_errors(self):
        for field, error_msg in self.errors.items():
            if field == "__all__":
                message = error_msg
            else:
                minus_asterisk = error_msg.as_text().replace("*", "").strip()
                message = "%s: %s" % (field, minus_asterisk)
            return HttpResponse(JSMessage(message, is_error=True))
