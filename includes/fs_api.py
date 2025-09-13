#!/usr/bin/python
"""
GCHUB Filesystem API
Handles finding, creating, deleting, re-naming, and interacting with files
so that the rest of the application doesn't have to.

NOTE: This file should not interact at all with any of our models. It is to be
completely independent from the database. This is important for the sake
of re-usability, especially for specialized purposes like Fedex and the
Rendering System.
"""

import datetime
import glob
import mimetypes
import os  # Operating System level things (files, dirs, etc)
import os.path
import re  # Regular Expressions
import shutil  # Shared utilities (recursive deletion)
import stat
import zipfile
from io import BytesIO
from socket import AF_INET, SOCK_DGRAM, socket
from subprocess import Popen

import exifread
from django.conf import settings
from django.utils import timezone

## ---------------------------------------------------------------------------
## Configuration
## ---------------------------------------------------------------------------
# Reset the shell's umask so it doesn't mess with NEWFILE_MODE.
os.umask(0)
# Default permissions mask for new files.
NEWFILE_MODE = 777
# Base path that the workflow folders reside in.
BASE_PATH = settings.WORKFLOW_ROOT_DIR
# Paths to the job directories for each workflow.
WORKFLOW_PATHS = {
    "Foodservice": os.path.join(BASE_PATH, "Foodservice"),
    "Beverage": os.path.join(BASE_PATH, "Beverage"),
    "Carton": os.path.join(BASE_PATH, "Carton"),
    "Container": os.path.join(BASE_PATH, "Containerboard"),
}
# A list of the folders under each workflow that contain job directories to search.
WORKFLOW_FOLDERS = ["Archive", "Active", "Completed"]
# Various directory constants. The keys are aliased names, the values are the
# subdirectory's full names. The keys for some start with numbers since the
# creation order matters if a folder has sub-folders.
JOBDIR = {
    "tiffs": "1_Bit_Tiffs",
    "1_documents": "Database_Documents",
    "2_approval_scans": "Database_Documents/Approval_Scans",
    "3_preview_art": "Database_Documents/Preview_Art",
    "4_print_seps": "Database_Documents/Printable_Separations",
    "proofs": "Proofs",
    "ref_files": "Reference_Files",
    "work_files": "Working_Files",
    "final_files": "Final_Files",
    "fonts": "Fonts",
}

# Used for thumbnailing various things. This is a hidden directory so we
# don't clutter Finder windows.
THUMBNAIL_FOLDER_NAME = ".thumbnails"

RENDER_PATHS = {
    "jpgs_for_render": "jpgs_for_render",
    "misc_files": "misc_files",
    "pov_models": "pov_models",
    "temp_files": "temp_files",
}

"""'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  Begin Exception definitions
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"""


class InvalidJob(Exception):
    """Thrown when a matching job folder can not be found."""

    def __str__(self):
        return "Specified Job file or directory cannot be found."


class InvalidItem(Exception):
    """Thrown when a matching item folder can not be found."""

    def __str__(self):
        return "Specified Item file or directory cannot be found."


class InvalidPath(Exception):
    """Thrown when an invalid or mal-formed path is provided."""

    def __str__(self):
        return "An invalid path has been provided."


class NoResultsFound(Exception):
    """Generic failure to match a search pattern."""

    def __str__(self):
        return "No files or directories matching the search pattern were found."


"""'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  Begin Methods
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"""


def get_beverage_drop_folder():
    """Return path to folder on Beverage for general uploads."""
    return settings.BEVERAGE_DROP_FOLDER


def get_fsb_templates_folder():
    """Return path to folder for FSB PDF templates.."""
    return settings.FSB_TEMPLATES


def get_fsb_production_templates_folder():
    """Return path to folder for FSB PDF templates.."""
    return settings.FSB_PROD_TEMPLATES


def get_job_folder(jobnum, validity_check=False):
    """
    Returns the folder matching a certain job number.
    This should only be one, but sometimes people leave stuff
    laying around in the directories that could confuse
    things.

    jobnum: (str) Job number to find the folder of.
    validity_check: (bool) When true, check to see if the job folder exists.
                           Return either the path as normal, or None if it
                           does not exist.
    """
    folder_str = os.path.join(settings.JOBSTORAGE_DIR, str(jobnum).zfill(5))
    if validity_check:
        if os.path.exists(folder_str):
            return folder_str
        else:
            raise InvalidJob()
    else:
        return folder_str


def find_job_folder(folder, jobnum):
    """
    Searches an arbitrary path for a job's folder.

    NOTE: This is much slower than get_job_folder() and should never be used
    unless there is a good reason!
    """
    pattern = re.compile(r"%s .*" % jobnum)
    # Build a list of the job folder's files. walk() returns a 3-tuple of
    # the root directory, the directories in the location, and the files in the
    # location. The third member of the tuple (2) is the directory list.
    contents_tuple = next(os.walk(folder))[1]
    # List comprehension builds matches list
    matches = [j_folder for j_folder in contents_tuple if pattern.search(j_folder)]

    try:
        retval = [os.path.join(folder, match) for match in matches]
        if retval:
            return retval[0]
        else:
            raise NoResultsFound()
    except IndexError:
        return None


def g_mkdir(folder_str):
    """Creates a directory, failing silently if it already exists."""
    try:
        os.mkdir(folder_str)
        return True
    except OSError as inst:
        # Directory already exists, but fail silently.
        if inst.errno == 17:
            return True
        else:
            raise


def create_job_folder(jobnum):
    """Creates the folder structure for a job."""
    folder_str = os.path.join(settings.JOBSTORAGE_DIR, str(jobnum))

    # Try to create the job folder.
    g_mkdir(folder_str)

    # Get the sub-folders and order them.
    folder_list = list(JOBDIR.keys())
    folder_list.sort()

    # Create job sub-folders.
    for folder in folder_list:
        g_mkdir(os.path.join(folder_str, JOBDIR[folder]))


def delete_job_folder(jobnum, fail_silently=True):
    """Deletes the job's entire folder structure recursively."""
    folder_str = get_job_folder(jobnum)
    try:
        shutil.rmtree(folder_str)
    except OSError as inst:
        # If the folder does not exist, but fail silently if asked to.
        if inst.errno == 2 and fail_silently:
            pass
        else:
            # Don't fail silently, re-raise preserving original traceback.
            raise


def _recursive_chmod(root_path, permission_bits):
    """
    Recursively chmod all of the files and directories (including the top)
    root_path. permission_bits is the 'mode' argument outlined by Py docs.

    Currently will ignore OSErrors on files and directories, but not the
    root path.
    """
    os.chmod(root_path, permission_bits)
    for root, dirs, files in os.walk(root_path):
        for name in files:
            try:
                os.chmod(os.path.join(root, name), permission_bits)
            except OSError:
                continue
        for name in dirs:
            try:
                os.chmod(os.path.join(root, name), permission_bits)
            except OSError:
                continue


def _send_fs_server_datagram(message):
    """Sends the FS server running on master a datagram."""
    addr = (settings.FS_SERVER_HOST, settings.FS_SERVER_PORT)
    s = socket(AF_INET, SOCK_DGRAM)

    num_sent = 0
    while num_sent < len(message):
        # encode makes this string byte-like so that s
        # (socket) can send the message that must be byte-like
        num_sent += s.sendto(message.encode(), addr)
    s.close()


def restart_fs_server():
    """Restarts the FS server."""
    _send_fs_server_datagram("shutdown")


def direct_lock_job_folder(jobnum):
    """
    Locks a job folder directly through filesystem calls.
    This is typically only done by master.
    """
    job_path = get_job_folder(jobnum)
    permission_bits = stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    _recursive_chmod(job_path, permission_bits)


def lock_job_folder(jobnum):
    """
    Calls on the GOLD FS server running on master to lock the specified
    job folder.
    """
    message = "lock_job_folder %s" % jobnum
    _send_fs_server_datagram(message)


def unlock_job_folder(jobnum):
    """
    Calls on the GOLD FS server running on master to unlock the specified
    job folder.
    """
    message = "unlock_job_folder %s" % jobnum
    _send_fs_server_datagram(message)


def direct_unlock_job_folder(jobnum):
    """
    Unlocks a job folder directly through filesystem calls.
    This is typically only done by master.
    """
    job_path = get_job_folder(jobnum)
    permission_bits = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
    _recursive_chmod(job_path, permission_bits)


def strip_for_valid_filename(filename):
    """
    Strips a string of all invalid characters that are unsuitable for
    file/directory names.

    TODO: Once we move to Python 2.6, we can use string.translate() as a MUCH
    faster alternative to this. Try not to use this function for anything
    done often, it's not very fast as it stands.
    """
    INVALID_CHARS = "~!@#$%^&*()=+:;'\"[]{}<>,.\\|/"
    newname = filename
    for char in INVALID_CHARS:
        newname = newname.replace(char, "")
    return newname


def get_jobnum_itemnum_finder_regexp(jobnum, itemnum, extension=None):
    """
    Returns the generic regular expression for finding things that match
    patterns similar to the following:

    53363-1
    53363-1 DMR-12
    """
    if not extension:
        return re.compile(r"(%s)-(%s)( |$)" % (jobnum, itemnum))
    else:
        return re.compile(r"(%s)-(%s)( .*\.%s$|\.%s$)" % (jobnum, itemnum, extension, extension))


def _generic_item_subfolder_search(folder, pattern):
    """A generic sub-folder job search. DRY."""
    # Build a list of the job folder's files. walk() returns a 3-tuple of
    # the root directory, the directories in the location, and the files in the
    # location. The third member of the tuple (2) is the directory list.
    try:
        contents_tuple = next(os.walk(folder))[1]
    except TypeError:
        # The value of 'folder' is probably an invalid path.
        # Mask underlying implementation details for callers.
        raise InvalidPath() from None
    except StopIteration:
        # The path could not be found, it's invalid.
        # Mask internal StopIteration details from higher layers.
        raise InvalidPath() from None
    # List comprehension builds matches list
    matches = [j_folder for j_folder in contents_tuple if pattern.search(j_folder)]

    try:
        retval = [os.path.join(folder, match) for match in matches]
        # No matches were found, kablooey.
        if retval:
            return retval[0]
        else:
            raise NoResultsFound()
    except IndexError:
        return None


def _generic_item_file_search(folder, pattern, return_first=True, excluded_files=[".DS_Store"]):
    """A generic sub-folder item search. DRY."""
    # Build a list of the job folder's files. walk() returns a 3-tuple of
    # the root directory, the directories in the location, and the files in the
    # location. The third member of the tuple (2) is the item list.
    try:
        contents_tuple = next(os.walk(folder))[2]
    except TypeError:
        # The value of 'folder' is probably an invalid path.
        raise InvalidPath() from None

    # List comprehension builds matches list
    matches = [j_file for j_file in contents_tuple if pattern.search(j_file)]

    try:
        # Make sure this match isn't one of the excluded files.
        retval = [os.path.join(folder, match) for match in matches if match not in excluded_files]

        # No matches were found, kablooey.
        if not retval:
            raise NoResultsFound()

        if return_first:
            # Returns the first match only.
            return retval[0]
        else:
            # Returns a list of matches
            return retval
    except IndexError:
        return None


def find_item_folder(jobnum, itemnum, search_dir="final_files"):
    """
    Returns the full path to the item's Final File subfolder.

    jobnum: (int) Job number
    itemnum: (int or str) Item number to find
    """
    pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    ff_folder = os.path.join(get_job_folder(jobnum), JOBDIR[search_dir])
    retval = _generic_item_subfolder_search(ff_folder, pattern)
    if retval is None:
        raise InvalidItem()
    return retval


def create_item_folder(jobnum, itemnum, itemname):
    """Creates the necessary folders for an item."""
    item_folder_str = "%s-%s %s" % (jobnum, itemnum, itemname)
    created_folders = []

    ff_folder_str = os.path.join(get_job_folder(jobnum), JOBDIR["final_files"], item_folder_str)
    created_folders.append(ff_folder_str)

    proof_folder_str = os.path.join(get_job_folder(jobnum), JOBDIR["proofs"], item_folder_str)
    created_folders.append(proof_folder_str)

    tiff_folder_str = os.path.join(get_job_folder(jobnum), JOBDIR["tiffs"], item_folder_str)
    created_folders.append(tiff_folder_str)

    for folder in created_folders:
        try:
            os.makedirs(folder)
        except OSError as inst:
            # Directory already exists, but fail silently.
            if inst.errno == 17:
                pass


def rename_item_folders(jobnum, itemnum, itemname):
    """
    Renmames the necessary folders for an item in the event of an
    intermixed job that has manual folder    creation components. This
    throws off the naming scheme and doesnt update folder names on the server.
    """
    oldName = "%s-%s" % (jobnum, itemnum)
    message = ""
    try:
        os.chdir(os.path.join(get_job_folder(jobnum), JOBDIR["final_files"]))
        oldFolder = glob.glob(oldName + "*")
        newName = "%s-%s %s" % (jobnum, itemnum, itemname)
        os.rename(oldFolder[0], newName)
    except Exception:
        message = "Error"

    try:
        os.chdir(os.path.join(get_job_folder(jobnum), JOBDIR["proofs"]))
        oldFolder = glob.glob(oldName + "*")
        newName = "%s-%s %s" % (jobnum, itemnum, itemname)
        os.rename(oldFolder[0], newName)
    except Exception:
        message = "Error"

    try:
        os.chdir(os.path.join(get_job_folder(jobnum), JOBDIR["tiffs"]))
        oldFolder = glob.glob(oldName + "*")
        newName = "%s-%s %s" % (jobnum, itemnum, itemname)
        os.rename(oldFolder[0], newName)
    except Exception:
        message = "Error"

    return message


def create_tiff_folder(jobnum, itemnum, itemname):
    """
    Creates a tiff folder for an item. This is primarily used by Backstage,
    and new jobs automatically get a tiffs folder.
    """
    item_folder_str = "%s-%s %s" % (jobnum, itemnum, itemname)
    tiffs_folder_str = os.path.join(get_job_folder(jobnum), JOBDIR["tiffs"], item_folder_str)
    # Create the folder
    g_mkdir(tiffs_folder_str)


def delete_item_folders(jobnum, itemnum):
    """
    Looks through a Job folder and deletes all of the specified item's folders
    recursively. Be careful with this!
    """
    pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    for dir in list(JOBDIR.values()):
        try:
            full_dir = os.path.join(get_job_folder(jobnum), dir)
            folder_str = _generic_item_subfolder_search(full_dir, pattern)

            # Delete the item's folder RECURSIVELY.
            shutil.rmtree(folder_str)
        except NoResultsFound:
            # No matching item folder was found under this directory.
            pass


def rename_item_folder(jobnum, itemnum, newname, remove_itemnum_prefix=False):
    """
    Re-names an item's folder.

    remove_itemnum_prefix: (bool) If True, don't include the item number in
    the beginning of the folder's name. This will avoid future conflicts when
    searching for job-itemnum folders.
    """
    folder_str = find_item_folder(jobnum, itemnum)

    if remove_itemnum_prefix:
        new_item_folder_name = "%s %s" % (jobnum, newname)
    else:
        new_item_folder_name = "%s-%s %s" % (jobnum, itemnum, newname)

    final_path = os.path.join(os.path.dirname(folder_str), new_item_folder_name)
    shutil.move(folder_str, final_path)


def get_item_finalfile_folder(jobnum, itemnum):
    """
    Returns the path to the item's production files folder under the
    Job/Final Files folder.
    For example: Final Files/51234-1 SMR-16/
    """
    # TODO: Replace this function with find_item_folder()
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["final_files"])
    try:
        pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    except Exception:
        raise
    return _generic_item_subfolder_search(folder, pattern)


def get_item_finalfile(jobnum, itemnum):
    """
    Return an item's production/final file PDF.
    JobFolder/Final_Files/jobnum-itemnum size/jobnum-itemnum.pdf
    (ie, Final_Files/51234-1 SMR-16/51234-1.pdf)
    """
    item_subfolder = get_item_finalfile_folder(jobnum, itemnum)

    pattern = re.compile(r"(.*)-(%s)( .*\.pdf$|\.pdf$)" % (itemnum))

    return _generic_item_file_search(item_subfolder, pattern)


def get_item_outputs_folder(jobnum, itemnum):
    """
    Return an item's "Outputs" folder. Carton items usually have these.
    For example: Final_Files/87968-1 Carton SBS/Outputs/
    """
    item_ff_folder = get_item_finalfile_folder(jobnum, itemnum)
    target_folder_name = "outputs"
    pattern = re.compile(r"(?i)%s" % (target_folder_name))  # Not case sensitive

    return _generic_item_subfolder_search(item_ff_folder, pattern)


def get_item_outputs(jobnum, itemnum):
    """
    Return an item's "Outputs" PDF file. Carton items usually have these.
    For example: Final_Files/87968-1 Carton SBS/Outputs/87968-1 59355A1_x1a.pdf
    """
    item_subfolder = get_item_outputs_folder(jobnum, itemnum)

    pattern = re.compile(r"(.*)-(%s)( .*\.pdf$|\.pdf$)" % (itemnum))

    return _generic_item_file_search(item_subfolder, pattern)


def get_item_deleteonoutput_folder(jobnum, itemnum):
    """
    Returns the path to the item's DeleteOnOutput folder under the
    Job/Final Files folder.
    For example: Final Files/84837-1 Carton CRB/DeleteOnOutput
    """
    item_ff_folder = get_item_finalfile_folder(jobnum, itemnum)
    target_folder_name = "deleteonoutput"
    pattern = re.compile(r"(?i)%s" % (target_folder_name))  # Not case sensitive

    return _generic_item_subfolder_search(item_ff_folder, pattern)


def delete_item_deleteonoutput_folder(jobnum, itemnum):
    """Deletes the item's entire DeleteOnOutput folder structure recursively."""
    try:
        folder_str = get_item_deleteonoutput_folder(jobnum, itemnum)
        shutil.rmtree(folder_str)
    except NoResultsFound:
        # No matching folder was found.
        pass


def make_thumbnail_item_finalfile(jobnum, itemnum, width=155):
    """
    Generates a thumbnail of an items final file PDF. This is put in a
    hidden directory under the item's final file folder.
    For example: Final Files/51234-1 SMR-16/.thumbnails/
    """
    ff_file = get_item_finalfile(jobnum, itemnum)
    ff_folder = get_item_finalfile_folder(jobnum, itemnum)
    # Figure out where the .thumbnails folder should be.
    thumbnail_folder = os.path.join(ff_folder, THUMBNAIL_FOLDER_NAME)
    # Create the .thumbnails folder if it doesn't already exist.
    g_mkdir(thumbnail_folder)
    thumbnail_file = os.path.join(thumbnail_folder, "thumb_%d.png" % width)
    cmd_list = ["/usr/bin/convert", "-thumbnail", str(width), ff_file, thumbnail_file]
    Popen(cmd_list).communicate()


def get_thumbnail_item_finalfile(jobnum, itemnum, width=155):
    """
    Retrieves the final file thumbnail for an item.

    Returns the string path to the thumbnail, or a None value if none can
    be found.
    """
    ff_folder = get_item_finalfile_folder(jobnum, itemnum)
    # Figure out where the .thumbnails folder should be.
    thumbnail_folder = os.path.join(ff_folder, THUMBNAIL_FOLDER_NAME)
    thumbnail_file = os.path.join(thumbnail_folder, "thumb_%d.png" % width)

    if os.path.exists(thumbnail_file):
        return thumbnail_file
    else:
        return None


def get_item_proof_folder(jobnum, itemnum):
    """
    Returns the path to the item's proofs folder under the Job/Proofs folder.
    For example: Proofs/51234-1 SMR-16/
    """
    # TODO: Replace this function with find_item_folder()

    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["proofs"])

    try:
        pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    except Exception:
        raise
    return _generic_item_subfolder_search(folder, pattern)


def copy_carton_imp_files(jobnum, itemnum, dest_jobnum, dest_itemnum):
    """
    Copies files needed when duplicating carton imposition jobs.
    For example:
        Final_Files/87968-1 Carton SBS/87968-1 59355A1_x1a.pdf
        Database_Documents/Approval_Scans/87968_1.pdf
    """
    # Final_File/Outputs
    try:
        # Source
        source_file = get_item_outputs(jobnum, itemnum)
        # Destination folder
        dest_folder = get_item_finalfile_folder(dest_jobnum, dest_itemnum)
        # Rename_destination file.
        source_filename = source_file.split("/")[-1]
        source_job_item = str(jobnum) + "-" + str(itemnum)
        dest_job_item = str(dest_jobnum) + "-" + str(dest_itemnum)
        dest_filename = source_filename.replace(str(source_job_item), str(dest_job_item))
        dest_file = os.path.join(dest_folder, dest_filename)
        # Copy
        shutil.copyfile(source_file, dest_file)
    except Exception:
        pass
    # Approval PDFs
    try:
        # Source
        source_pdf = get_item_approval_pdf(jobnum, itemnum)
        # Destination folder
        dest_jobfolder = get_job_folder(dest_jobnum)
        dest_preview_folder = os.path.join(dest_jobfolder, JOBDIR["3_preview_art"])
        # Rename_destination file.
        source_pdfname = source_pdf.split("/")[-1]
        source_job_item = str(jobnum) + "_" + str(itemnum)
        dest_job_item = str(dest_jobnum) + "_" + str(dest_itemnum)
        dest_pdfname = source_pdfname.replace(str(source_job_item), str(dest_job_item))
        dest_pdfname = "ap_" + dest_pdfname
        dest_pdf = os.path.join(dest_preview_folder, dest_pdfname)
        # Copy
        shutil.copyfile(source_pdf, dest_pdf)
    except Exception:
        pass


def copy_carton_diestruct(jobnum, dest_jobnum, diename):
    """
    Copies 1up die structure files needed when duplicating carton imposition
    jobs. Usually a PDF and an EPS file.
    For example:
        Reference_Files/59355A1 [Converted].pdf
        Reference_Files/59355A1.EPS
    """
    try:
        source_jobfolder = get_job_folder(jobnum)
        source_ref_folder = os.path.join(source_jobfolder, JOBDIR["ref_files"])
        dest_jobfolder = get_job_folder(dest_jobnum)
        dest_ref_folder = os.path.join(dest_jobfolder, JOBDIR["ref_files"])
        try:
            # PDF
            pdf_pattern = re.compile(r"(^%s)( .*\.(?i)pdf$|\.(?i)pdf$)" % (diename))
            source_pdf = _generic_item_file_search(source_ref_folder, pdf_pattern)
            shutil.copy(source_pdf, dest_ref_folder)
        except Exception:
            pass
        try:
            # EPS
            eps_pattern = re.compile(r"(^%s)( .*\.(?i)eps$|\.(?i)eps$)" % (diename))
            source_eps = _generic_item_file_search(source_ref_folder, eps_pattern)
            shutil.copy(source_eps, dest_ref_folder)
        except Exception:
            pass
    except Exception:
        pass


def copy_item_proof_folder(jobnum, itemnum, proof_log_id):
    """Copies the entire item proof folder so that a revision history is maintained."""
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["proofs"])
    try:
        pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    except Exception:
        raise
    proof_folder = _generic_item_subfolder_search(folder, pattern)
    proof_copy_folder = os.path.join(
        proof_folder,
        str("%s %s_%s %s" % ("Previous Proofs", str(jobnum), str(itemnum), str(proof_log_id))),
    )
    shutil.copytree(proof_folder, proof_copy_folder)


def get_item_proof(jobnum, itemnum, quality=None, proof_log_id=None, return_first=True):
    """
    Return an item's approval or print card proof file.
    JobFolder/Proofs/jobnum-itemnum size/jobnum-itemnum.pdf
    (ie, Proofs/51234-1 SMR-16/51234-1.pdf)

    quality: (string) 'h' for high quality, 'l' for low quality,
    or None for neither.
    """
    item_subfolder = get_item_proof_folder(jobnum, itemnum)

    if proof_log_id:
        item_subfolder = os.path.join(
            item_subfolder,
            str("%s %s_%s %s" % ("Previous Proofs", str(jobnum), str(itemnum), str(proof_log_id))),
        )

    # If quality is 'l', 'h' or anything else, match that here.
    if quality:
        pattern = re.compile(r"(.*)-(%s)( .*%s\.pdf$|%s\.pdf$)" % (itemnum, quality, quality))
    else:
        # This is usually Foodservice, who has no -l.pdf suffix.
        pattern = re.compile(r"(.*)-(%s)( .*\.pdf$|\.pdf$)" % (itemnum))

    return _generic_item_file_search(item_subfolder, pattern, return_first=return_first)


def get_item_approval_pdf(jobnum, itemnum):
    """
    Pulls the approval PDF for a given item.
    JobFolder/DatabaseDocs/Approvals/xxx.pdf
    Only exists for FSB, and even then, not all the time.
    Will need to first check the job folder directories,
    then look on the archive server for it.
    """
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["2_approval_scans"])
    pattern = re.compile(r"(.*)_(%s)[.](pdf)$" % itemnum)
    return _generic_item_file_search(folder, pattern)


def get_item_preview_art(jobnum, itemnum):
    """
    Pulls the preview artwork for a given item.
    JobFolder/DatabaseDocs/Preview/ap_jobnum_itemnum.pdf
    Will need to first check the job folder directories, then look on the archive server for it.
    """
    # Check if file system access is disabled for development
    if not getattr(settings, "FS_ACCESS_ENABLED", True):
        # Mock preview art for development environment
        raise NoResultsFound("Preview art access disabled in development mode")

    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["3_preview_art"])
    pattern = re.compile(r"ap_(.*)_(%s)[.](pdf)$" % itemnum)
    return _generic_item_file_search(folder, pattern)


def get_item_print_seps(jobnum, itemnum):
    """
    Pulls the printable separations pdf for a given item.
    JobFolder/Database_Documents/Printable_Separations/jobnum-itemnum_size_Seps.pdf
    """
    # Check if file system access is disabled for development
    if not getattr(settings, "FS_ACCESS_ENABLED", True):
        # Mock print separations for development environment
        raise NoResultsFound("Print separations access disabled in development mode")

    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["4_print_seps"])
    pattern = re.compile(r"(.*)-(%s)_(.*)_Seps[.](pdf)$" % itemnum)
    return _generic_item_file_search(folder, pattern)


def get_item_3drender(jobnum, itemnum):
    """
    Not sure where this will come from...
    Me neither.
    """
    pass


def get_item_3drender_texture(jobnum, itemnum):
    """
    Returns the path to the item's 3D render texture JPG. If no matches are
    found, return None.
    """
    jpg_path = os.path.join(
        settings.RENDERSYS_ROOT,
        RENDER_PATHS["jpgs_for_render"],
        "%s-%s.jpg" % (jobnum, itemnum),
    )

    if os.path.exists(jpg_path):
        return jpg_path
    else:
        return None


def get_mimetype(file):
    """Return mimetype of given file."""
    type = mimetypes.guess_type(file)
    return type[0]


def list_job_database_docs(jobnum):
    """
    Non-item specific. Could be PDF, JPG, TXT, ???
    JobFolder/DatabaseDocs/*  (anything not in approval or preview subfolders)
    """
    doc_list = []
    try:
        jobfolder = get_job_folder(jobnum)
        folder = os.path.join(jobfolder, JOBDIR["1_documents"])
        # Match any file
        pattern = re.compile(r".*$")

        documents = _generic_item_file_search(folder, pattern, return_first=False)

        for doc in documents:
            doc_list.append(
                {
                    "file_name": doc.split("/")[-1:][0],
                    "file_path": doc,
                    "last_modified_time": datetime.datetime.utcfromtimestamp(os.path.getmtime(doc)),
                    "file_size": os.path.getsize(doc),
                }
            )
    except Exception:
        pass

    return doc_list


def escape_string_for_regexp(input_str):
    """Escapes a string for use with a regular expression."""
    escape_chars = ["(", ")", "[", "]"]
    for char in escape_chars:
        input_str = input_str.replace(char, "\\" + char)
    return input_str


def get_job_database_doc(jobnum, filename):
    """Retrieves a document's full path for retrieval via a view."""
    # Path to the Database Documents directory
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["1_documents"])
    cleaned_filename = escape_string_for_regexp(filename)
    pattern = re.compile(r"%s$" % cleaned_filename)
    return _generic_item_file_search(folder, pattern)


def get_job_database_path(jobnum):
    """Retrieves the full path of the documents folder"""
    # Path to the Database Documents directory
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["1_documents"])
    return folder


def get_pdf_template(size):
    """Return specific file for a requested size."""
    folder = os.path.join(settings.FSB_TEMPLATES)
    pattern = re.compile(r"(%s)( .*\.pdf$|\.pdf$)" % (size))
    return _generic_item_file_search(folder, pattern)


def get_pdf_templates():
    """Return a dictionary of information about each pdf in the templates directory."""
    folder = get_fsb_templates_folder()

    contents_list = os.listdir(folder)
    # pattern = re.compile(r'(.*).pdf')
    pattern = re.compile(r".*.pdf")
    pdfs = [pdf_file for pdf_file in contents_list if pattern.search(pdf_file)]

    return pdfs


def get_fsb_production_template(size_name, product_type, plantcode, press_shortname):
    """
    Given the size and printlocation (plant and press), return the appropriate
    production template file.
    """
    folder = get_fsb_production_templates_folder()
    # Set subfolder based on product type (Hot Cup, Cold Cup, Food Packaging)
    folder = os.path.join(folder, product_type)
    # Note: the (?i)%s mean look for case insensitve match to the %s string.
    # print( product_type, size_name, plantcode, press_shortname)
    pattern = re.compile(r"((?i)%s-%s(?i)%s)( .*\.pdf$|\.pdf$)" % (size_name, str(plantcode), press_shortname))
    template = _generic_item_file_search(folder, pattern)
    return template


def copy_fsb_production_template(size_name, product_type, plantcode, press_shortname, jobnum, itemnum):
    """Get and copy the FSB productuion template into the item Final Files subfolder."""
    pdf_template = get_fsb_production_template(size_name, product_type, plantcode, press_shortname)
    # Will be placing the PDF into the item's Final File subfolder.
    item_subfolder = get_item_finalfile_folder(jobnum, itemnum)
    # eg: 59300-2 DMR-22-45FK.pdf"
    pdf_name = "%s-%s %s-%s%s" % (
        str(jobnum),
        str(itemnum),
        size_name,
        str(plantcode),
        press_shortname,
    )
    cleaned_filename = escape_string_for_regexp("%s%s" % (pdf_name, ".pdf"))
    pattern = re.compile(r"(?i)%s$" % cleaned_filename)

    # Append the timestamp if a file already exists with that name.
    try:
        _generic_item_file_search(item_subfolder, pattern)
        pdf_name += "%s%s" % (timezone.now().strftime("%m_%d_%y-%H_%M"), ".pdf")
    except NoResultsFound:
        pdf_name += ".pdf"

    item_pdf_path = os.path.join(item_subfolder, pdf_name)
    shutil.copy(pdf_template, item_pdf_path)


def list_item_tiffs(jobnum, itemnum):
    """
    Return a dictionary of information about each tiff in an item's tiffs
    directory.
    """
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["tiffs"])
    pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    tiffs_folder = _generic_item_subfolder_search(folder, pattern)

    # No tiffs folder, no tiffs.
    if not tiffs_folder:
        return None

    contents_list = os.listdir(tiffs_folder)
    tiff_pattern = re.compile(r"(.*).tif")
    len_pattern = re.compile(r"(.*).len")
    tiffs = [tiff_file for tiff_file in contents_list if tiff_pattern.search(tiff_file) or len_pattern.search(tiff_file)]

    tiff_list = []
    for tiff in tiffs:
        # Combined for ease of access
        tiff_full_path = os.path.join(tiffs_folder, tiff)
        try:
            # Parse the Tiff file. If for some reason it can't be opened,
            # ignore this file as it's probably not a tiff.
            exif_info = exifread.process_file(open(tiff_full_path, "rb"))
        except IOError:
            print("IOError, continuing.")
            continue

        mod_time = os.path.getmtime(tiff_full_path)
        mod_time = datetime.datetime.utcfromtimestamp(mod_time)

        file_size = os.path.getsize(tiff_full_path)

        # It looks like our RIP uses pixels/inch. If this should ever change,
        # we'd need to pull the resolution unit.
        # tiff_resolution_unit exif_info["Image ResolutionUnit"].values
        try:
            """
            Sometimes this fails due to badly formed tifs. In this case,
            don't populate the resolution keys, but still return the file
            information.
            """
            image_resolution = float(exif_info["Image XResolution"].values[0].num)
            image_width = exif_info["Image ImageWidth"].values[0]
            image_width_inches = image_width / image_resolution
            image_length = exif_info["Image ImageLength"].values[0]
            image_length_inches = image_length / image_resolution
            image_area = image_width_inches * image_length_inches
        except KeyError:
            """
            Still populate the keys, just return None values so the other end
            knows something is up.
            """
            image_width_inches = None
            image_length_inches = None
            image_area = None

        tiff_list.append(
            {
                "file_name": tiff,
                "file_path": tiff_full_path,
                "last_modified_time": mod_time,
                "file_size": file_size,
                "image_width": image_width_inches,
                "image_length": image_length_inches,
                "image_area": image_area,
            }
        )

    return tiff_list


def get_item_tiff_path(jobnum, itemnum, filename):
    """
    Retrieves a tiff's full path for retrieval via a view.
    filename: (string) Either the file name or a regex string
    """
    # Path to the 1_Bit_Tiffs directory
    jobfolder = get_job_folder(jobnum)
    folder = os.path.join(jobfolder, JOBDIR["tiffs"])

    # Find the item's sub-folder
    pattern = get_jobnum_itemnum_finder_regexp(jobnum, itemnum)
    tiffs_folder = _generic_item_subfolder_search(folder, pattern)

    # Search for tiffs
    pattern = re.compile(r"%s$" % filename)
    return _generic_item_file_search(tiffs_folder, pattern)


def get_zip_all_tiffs(jobnum, itemnum):
    """Return a zip file for download of all the tiffs with an item."""
    # Get the tiff info dictionary
    tiff_list = list_item_tiffs(jobnum, itemnum)
    # This is a file-like object that we can write() and read() from.
    temp_file = BytesIO()
    # zipfile uses the BytesIO object for storage
    zipped_tiff_file = zipfile.ZipFile(temp_file, "w", zipfile.ZIP_DEFLATED)

    # Add each of the tiffs to the Zip file.
    for tiff in tiff_list:
        # This creates a zip file which unzips correctly (1 folder w/ tiffs inside)
        zipped_tiff_file.write(tiff["file_path"], tiff["file_name"], zipfile.ZIP_DEFLATED)
    # Absolutely critical to close the zip file before reading it. Causes
    # the reference tables to be written, resulting in a readable ZIP archive.
    zipped_tiff_file.close()
    # See BytesIO documentation. Reads contents of BytesIO without requiring
    # that it be close()'d first.
    return temp_file.getvalue()


def get_ftp_plate_files(jobnum, itemnum):
    """
    Return a zip file containing all of an items tiffs and the low res proof
    file. Suitable for uploading to an FTP server.
    """
    # Get the tiff info dictionary
    tiff_list = list_item_tiffs(jobnum, itemnum)
    # This is a file-like object that we can write() and read() from.
    temp_file = BytesIO()
    # zipfile uses the BytesIO object for storage
    zipped_tiff_file = zipfile.ZipFile(temp_file, "w", zipfile.ZIP_DEFLATED)

    # Add each of the tiffs to the Zip file.
    for tiff in tiff_list:
        # This creates a zip file which unzips correctly (1 folder w/ tiffs inside)
        zipped_tiff_file.write(tiff["file_path"], tiff["file_name"], zipfile.ZIP_DEFLATED)

    # Add the low res proof to the Zip file.
    try:
        # Returns the path to the item's low res proof.
        proof_file_path = get_item_proof(jobnum, itemnum, quality="l")
        # Yank the '-l' out of the file name for the remote copy.
        proof_remote_filename = os.path.split(proof_file_path)[1].replace("-l.pdf", ".pdf")
        zipped_tiff_file.write(proof_file_path, proof_remote_filename, zipfile.ZIP_DEFLATED)
    except Exception:
        pass

    # Absolutely critical to close the zip file before reading it. Causes
    # the reference tables to be written, resulting in a readable ZIP archive.
    zipped_tiff_file.close()
    # See BytesIO documentation. Reads contents of BytesIO without requiring
    # that it be close()'d first.
    return temp_file


def list_job_proofs(jobnum, itemcount):
    """
    Return a dictionary of information (filename and path) about each proof in
    a job.
    """
    proof_dict = []
    # Count through all items in the job and add their proofs to the dictionary.
    while itemcount > 0:
        try:
            path = get_item_proof(jobnum, itemcount, "l")
            filename = str(jobnum) + "-" + str(itemcount) + "_proof.pdf"
            proof_dict.append({"file_name": filename, "file_path": path})
        except Exception:
            pass
        itemcount = itemcount - 1
    return proof_dict


def get_zip_all_proofs(jobnum, itemcount):
    """Return a zip file for download of all the proofs with a job."""
    # Get the proofs' info dictionary
    proof_list = list_job_proofs(jobnum, itemcount)
    # Check if there are actually any proofs first.
    if len(proof_list) > 0:
        # This is a file-like object that we can write() and read() from.
        temp_file = BytesIO()
        # zipfile uses the BytesIO object for storage
        zipped_proof_file = zipfile.ZipFile(temp_file, "w", zipfile.ZIP_DEFLATED)
        # Add each of the proofs to the Zip file.
        for proof in proof_list:
            # Create a zip file which unzips correctly (1 folder w/ proofs inside)
            zipped_proof_file.write(proof["file_path"], proof["file_name"], zipfile.ZIP_DEFLATED)
        # Absolutely critical to close the zip file before reading it. Causes
        # the reference tables to be written, resulting in a readable ZIP archive.
        zipped_proof_file.close()
        # See BytesIO documentation. Reads contents of BytesIO without requiring
        # that it be close()'d first.
        return temp_file.getvalue()
    else:
        return False
