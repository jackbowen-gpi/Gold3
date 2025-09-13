"""Address book application -  handles contacts."""

from django.db import models

from gchub_db.apps.fedexsys.models import AddressValidationModel


class Contact(AddressValidationModel):
    """A contact in the address book."""

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=255)
    country = models.CharField(max_length=255, default="US")
    phone = models.CharField(max_length=255)
    ext = models.CharField(max_length=25, blank=True)
    fax = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    active = models.BooleanField(default=1)

    def __str__(self):
        """String representation."""
        return self.get_full_name()

    def get_zip_code(self):
        """
        Needed in order to bridge some differences between the Contact and
        JobAddress models.
        """
        return self.zip_code

    # Preserve compatibility with JobAddress
    zip = property(get_zip_code)

    def get_full_name(self):
        """Returns first + last name."""
        return "%s %s" % (self.first_name, self.last_name)

    # Preserve compatibility with JobAddress
    name = property(get_full_name)

    def get_job_title(self):
        """
        Needed in order to bridge some differences between the Contact and
        JobAddress models.
        """
        return self.job_title

    # Preserve compatibility with JobAddress
    title = property(get_job_title)

    class Meta:
        ordering = ["last_name"]
