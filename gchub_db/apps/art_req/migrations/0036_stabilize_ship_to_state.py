"""Stabilize ship_to_state choices to prevent repeated autodetector churn.

This migration sets a consistent tuple literal for the `ship_to_state` field
choices so future `makemigrations` calls won't keep generating trivial
AlterField migrations due to differing serializations (list vs tuple vs
string). It mirrors the values in `state_choices.py`.
"""

from django.db import migrations, models

STATE_CHOICES = (
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AS", "American Samoa"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("AA", "Armed Forces Americas"),
    ("AE", "Armed Forces Europe"),
    ("AP", "Armed Forces Pacific"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("DC", "District of Columbia"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("GU", "Guam"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("MP", "Northern Mariana Islands"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("PR", "Puerto Rico"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VI", "Virgin Islands"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
)


class Migration(migrations.Migration):
    dependencies = [
        ("art_req", "0035_alter_product_ship_to_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="ship_to_state",
            field=models.CharField(
                blank=True,
                choices=STATE_CHOICES,
                max_length=2,
                verbose_name="Ship to State",
            ),
        ),
    ]
