#!/usr/bin/python
"""Import item reviews into GOLD from external sources and produce reports."""
import bin_functions

bin_functions.setup_paths()
from gchub_db.apps.workflow.models import Item, ItemReview

current_items = Item.objects.filter(job__workflow__name="Foodservice")[:5]

for item in current_items:
    # Plant Review
    plant_review = ItemReview()
    plant_review.item = item
    plant_review.review_catagory = "plant"
    plant_review.comments = item.plant_comments
    plant_review.reviewer = item.plant_reviewer
    plant_review.review_date = item.plant_review_date
    if item.plant_comments == "Accepted":
        plant_review.review_ok = True
    plant_review.save()
    # Demand Review

    # Marketing Review

    pass
