"""Custom model fields."""

from django.conf import settings
from django.core import exceptions
from django.db.models import fields
from django.utils.translation import gettext as _


class BigIntegerField(fields.IntegerField):
    def db_type(self, connection):
        if settings.DATABASES["default"]["ENGINE"] == "mysql":
            return "bigint"
        elif settings.DATABASES["default"]["ENGINE"] == "oracle":
            return "NUMBER(19)"
        elif settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql_psycopg2":
            return "bigint"
        else:
            # Default to a generic integer type for databases like SQLite
            # which don't have a separate BIGINT type.
            return "integer"

    def get_internal_type(self):
        return "BigIntegerField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError) as ex:
            raise exceptions.ValidationError(_("This value must be a long integer.")) from ex
