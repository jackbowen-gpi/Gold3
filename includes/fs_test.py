#!/usr/bin/env python
import os
import os.path
import sys

# Setup the Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.settings"

# Back to the ordinary imports
from . import fs_api

"""
Test stuff for fs_api. We'll eventually move this to a better location.
"""

# fs_api.delete_job_folder(61234)
# fs_api.create_job_folder(61234)
# fs_api.create_item_folder(61234, 1, "Test Item")
# fs_api.create_item_folder(61234, 2, "Another Test")
# fs_api.rename_item_folder(61234, 2, "Rename Test")
# print fs_api.find_job_folder("/Volumes/FoodserviceB/Active", 49297)
# fs_api.delete_item_folder(61234, 1)
# print "FSB Search"
# jobfolder = fs_api.find_job_folder(61234, validity_check=False)
# print jobfolder
# print jobfolder
# itemfolder = fs_api.find_item_folder(jobfolder, 1)
# print itemfolder
# print fs_api.get_item_proof(54786, 1, quality=None)
# print fs_api.get_item_approval_pdf(jobfolder, 1)
# print fs_api.get_item_preview_art(54786, 1)
# print fs_api.list_job_database_docs(jobfolder)
# print fs_api.get_job_database_doc(jobfolder, "test")
# print fs_api.find_item_folder(53363, 1)
# import os.path
# print os.path.split(fs_api.get_item_proof(53363, 1, quality='l'))[1].replace('-l.pdf','.pdf')
# print fs_api.list_item_tiffs(54540, 1)
# print fs_api.find_item_folder(54816, 1, search_dir='proofs')
# print fs_api.get_item_tiff_path(53363, 1, '53363-1 70F-710-213-53363_123.tif')
# print fs_api.get_item_tiff_path(jobfolder, 1, "51785-1 smr-4-33in_DQPO4115N.tif")
# print "Unspecified Search"
# print fs_api.find_jobfolder(53430)
# print fs_api.escape_string_for_regexp("44988Spec Sheet(s).pdf")
# fs_api.unlock_job_folder(99999)
fs_api.make_thumbnail_item_finalfile(57168, 1)
# print fs_api.get_thumbnail_item_finalfile(57140,1)
