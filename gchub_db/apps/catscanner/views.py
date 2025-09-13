from string import Template

from django.http import HttpResponse

from gchub_db.apps.workflow.models import Job


def item_data(request, job_id, item_num):
    """
    Return item data for Catscanner to parse.

    URL: /catscanner/item_data/<job_id>/<item_num>/
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return HttpResponse("invalid_job")

    if str(item_num) == "0":
        # This typically happens on scan errors.
        return HttpResponse("invalid_item")

    try:
        item = job.get_item_num(item_num)
    except IndexError:
        return HttpResponse("invalid_item")

    colors = item.itemcolor_set.all()
    num_colors = colors.count()

    color_list = [color.color for color in colors]
    color_list_str = "|".join(color_list)

    response_template = Template("$item_id|$job_name|$item_size|$num_colors|$colors")
    return HttpResponse(
        response_template.substitute(
            item_id=item.id,
            job_name=job.name,
            item_size=item.size.size,
            num_colors=num_colors,
            colors=color_list_str,
        )
    )


def color_data(request, job_id, item_num, color_num):
    """Returns color data for an item's color."""
    job = Job.objects.get(id=job_id)
    item = job.get_item_num(item_num)
    colors = item.itemcolor_set.all()
    # Get the ItemColor matching the specified index in the color array.
    color = colors[int(color_num)]
    # Shortened name
    colordef = color.definition

    if colordef is None:
        # No color definition found for this ItemColor. Don't compare it.
        return HttpResponse("1|0.0|0.0|0.0")
    else:
        # Some colors are not for comparison. QPO, Process, etc.
        if colordef.do_compare:
            dont_compare = 0
        else:
            dont_compare = 1

        return HttpResponse("%d|%f|%f|%f" % (dont_compare, colordef.lab_l, colordef.lab_a, colordef.lab_b))


def send_measurement(request, job_id, item_num, color_num):
    """
    Records a measurement to one of the ItemColor objects associated with an
    item.

    URL: /catscanner/send_measurement/<job_id>/<item_num>/<color_num>/

    Required GET Keys:
     * passes
     * delta_e
     * lab_l
     * lab_a
     * lab_b
    Optional GET Keys:
     * proof_out_override_reason
    """
    job = Job.objects.get(id=job_id)
    item = job.get_item_num(item_num)
    colors = item.itemcolor_set.all()
    color = colors[int(color_num)]

    pass_fail = request.GET["passes"]
    if pass_fail == "yes":
        color.delta_e_passes = True
    else:
        color.delta_e_passes = False

    color.delta_e = float(request.GET["delta_e"])
    color.measured_lab_l = float(request.GET["lab_l"])
    color.measured_lab_a = float(request.GET["lab_a"])
    color.measured_lab_b = float(request.GET["lab_b"])
    color.proof_out_override_reason = request.GET.get("proof_out_override_reason", None)
    color.save()

    return HttpResponse("success")
