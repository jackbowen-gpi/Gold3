"""Manager Tool Functions. These are functions that need to be accessed outside of
maager tools. We split them out to minimize circular dependencies.
"""

from gchub_db.apps.timesheet.models import TimeSheet
from gchub_db.apps.workflow.app_defs import COMPLEXITY_OPTIONS
from gchub_db.apps.workflow.models import Item, JobComplexity


def get_job_average_hours(supplied_category, supplied_type, supplied_artist=False):
    """Calculates the average amount of time artists put into a given type of job
    based on time sheet data. Averages are calculated for every available
    complexity for a given category and type. Results can be limited to a single
    artist if one is supplied.

    For example, this will tell you a creative, cost avoidance job averages 3
    hours at A complexity, 2.5 hours at B complexity, and 1 hour at C complexity.

    The data is returned as a list of tuples like this:
        [('URL', "this/that"), ('A', 0.5), ('B', 1.11), ('C', 0.72)]

    The first item is a partial URL for linking to a detailed report. The rest
    is the data.
    """
    # Master data list.
    data = []

    # First we append a partial URL for linking to a detailed report.
    partial_url = "%s/%s" % (supplied_category, supplied_type)
    data.append(("URL", partial_url))

    # Go through all the available complexities:
    for current_complexity in COMPLEXITY_OPTIONS:
        # Just the first part of the tuple is needed.
        current_complexity = current_complexity[0]

        # Get the job complexity objects.
        job_complexities = JobComplexity.objects.filter(
            category=supplied_category, complexity=current_complexity
        )

        # Filter by type next
        job_list = []
        # Limit to one artists if one is specified.
        if supplied_artist:
            for job_complexity in job_complexities:
                if job_complexity.job.type == supplied_type:
                    if job_complexity.job.artist == supplied_artist:
                        job_list.append(job_complexity.job)
        else:
            for job_complexity in job_complexities:
                if job_complexity.job.type == supplied_type:
                    job_list.append(job_complexity.job)

        # Calculate average total time from time sheets.
        total_hours = 0

        # Iterate through jobs and count the hours.
        for job in job_list:
            timesheets = TimeSheet.objects.filter(job=job)
            for sheet in timesheets:
                total_hours += sheet.hours

        # Calculate the average time.
        if len(job_list) > 0:
            total = total_hours / len(job_list)
            average_hours = round(total, 2)
        else:
            average_hours = 0

        # Add the data to the list as a complexity/hours tuple.
        data.append((str(current_complexity), str(average_hours)))

    return data


def get_item_average_hours(supplied_category, supplied_type, supplied_artist=False):
    """Just like get_job_average_hours but it takes the number of items into
    account. If you're using this to more accurately figure out how long a job
    will take remember multiply the results by the number of items in the job.

    The data is returned as a list of tuples like this:
        [('URL', "this/that"), ('A', 0.5), ('B', 1.11), ('C', 0.72)]
    """
    # Master data list.
    data = []

    # First we append a partial URL for linking to a detailed report.
    partial_url = "%s/%s" % (supplied_category, supplied_type)
    data.append(("URL", partial_url))

    # Go through all the available complexities:
    for current_complexity in COMPLEXITY_OPTIONS:
        # Just the first part of the tuple is needed.
        current_complexity = current_complexity[0]

        # Get the job complexity objects.
        job_complexities = JobComplexity.objects.filter(
            category=supplied_category, complexity=current_complexity
        )

        # Filter by type next
        job_list = []
        # Limit to one artists if one is specified.
        if supplied_artist:
            for job_complexity in job_complexities:
                if job_complexity.job.type == supplied_type:
                    if job_complexity.job.artist == supplied_artist:
                        job_list.append(job_complexity.job)
        else:
            for job_complexity in job_complexities:
                if job_complexity.job.type == supplied_type:
                    job_list.append(job_complexity.job)

        # Calculate average total time from time sheets.
        total_hours = 0
        total_items = 0

        # Iterate through jobs and count the hours and items.
        for job in job_list:
            # Count the items
            items = Item.objects.filter(job=job)
            total_items += items.count()
            # Count the hours
            timesheets = TimeSheet.objects.filter(job=job)
            for sheet in timesheets:
                total_hours += sheet.hours

        # Calculate the average time.
        if total_items > 0:
            total = total_hours / total_items
            average_hours = round(total, 2)
        else:
            average_hours = 0

        # Add the data to the list as a complexity/hours tuple.
        data.append((str(current_complexity), str(average_hours)))

    return data
