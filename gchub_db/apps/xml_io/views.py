"""XML (JDF/JMF) views"""

from django.http import HttpResponse

from gchub_db.apps.workflow.models import Job


def echo_input(request):
    """Prints the POST and GET dictionaries."""
    #    print "GET: %s\r\nPOST: %s\r\nFILES: %s\r\nRPOST: %s" % (request.GET,
    #                                                            request.POST,
    #                                                            request.FILES,
    #                                                            request.raw_post_data)
    print("\r\n" * 2)
    print(list(request.REQUEST.items()))
    return HttpResponse("")


def run_jdf_jobitem(request, job_id, item_num, genxml_func):
    """
    Executes a JDF task via hotolder. genxml_func must match a do_jdf_* function
    in workflow/models.py for this to work. See the comments for
    generate_jdf_jobitem() in this module for more details.
    """
    job = Job.objects.get(id=int(job_id))
    item = job.get_item_num(int(item_num))

    # Get a reference to the correct do_jdf function.
    jdf_method = getattr(item, "do_jdf_%s" % genxml_func, None)

    if jdf_method:
        # Fire off the retrieved JDF method from Item.
        jdf_method()
        return HttpResponse("Submitted")
    else:
        return HttpResponse("Invalid JDF Function")


def run_jmf_jobitem(request, job_id, item_num, genxml_func):
    """
    Executes a JDF task via JMF. genxml_func must match a genxml_jdf_* function
    in workflow/models.py for this to work. See the comments for
    generate_jdf_jobitem() in this module for more details.
    """
    job = Job.objects.get(id=int(job_id))
    item = job.get_item_num(int(item_num))
    item.submit_jmf_queue(genxml_func)
    return HttpResponse("Submitted")


def generate_jdf_jobitem(request, job_id, item_num, genxml_func):
    """
    Generates a JDF for the specified item, where genxml_func matches up to one
    of the genxml_jdf_* functions in workflow/models.py. For example, if you
    want to get the return value of genxml_jdf_fsb_proof, the url would
    look something like: http://somehost/xml/jdf/49297/1/fsb_proof

    NOTE: There is no trailing slash here, Backstage doesn't like trailing
    slashes for some retarded reason.
    """
    job = Job.objects.get(id=int(job_id))
    item = job.get_item_num(int(item_num))
    # Get the genxml_jdf_* function that matches genxml_func as a reference.
    genxml = getattr(item, "genxml_jdf_" + genxml_func)
    # Run the function and pipe it out to the client as a JDF file.
    return HttpResponse(genxml().get_xml_doc_string(pretty=False), content_type="vnd.cip4-jdf+xml")
