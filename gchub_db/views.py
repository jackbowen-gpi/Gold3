from django.shortcuts import render
from django.http import HttpResponse


def test_standard_template(request):
    try:
        return render(request, "standard.html")
    except Exception as e:
        return HttpResponse(f"Error loading template: {e}", status=500)
