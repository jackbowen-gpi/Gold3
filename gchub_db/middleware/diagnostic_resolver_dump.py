r"""
Module gchub_db\middleware\diagnostic_resolver_dump.py
"""

import os

from django.urls import get_resolver

from includes.general_funcs import _utcnow_naive


class DiagnosticResolverDumpMiddleware:
    """
    Middleware to dump URL resolver reverse_dict and top-level patterns.

    Enabled only when the environment variable DIAG_RESOLVER=1. Writes a
    small text file under the project root named resolver_dump_<pid>.txt.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Dump only for workflow-related paths to reduce noise
        if os.environ.get("DIAG_RESOLVER") == "1" and request.path.startswith("/workflow"):
            try:
                resolver = get_resolver(None)
                pid = os.getpid()
                now_dt = _utcnow_naive()
                now = now_dt.strftime("%Y%m%dT%H%M%S")
                fname = os.path.abspath(os.path.join(os.getcwd(), f"resolver_dump_{pid}_{now}.txt"))
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(f"Resolver dump for pid={pid} path={request.path}\n")
                    f.write("Reverse dict keys:\n")
                    try:
                        keys = list(resolver.reverse_dict.keys())
                    except Exception as e:
                        f.write(f"  (error reading reverse_dict: {e})\n")
                        keys = []
                    for k in keys:
                        f.write(f"  {repr(k)}\n")
                    f.write("\nTop-level url pattern reprs:\n")
                    for p in resolver.url_patterns:
                        f.write(f"  {repr(p)}\n")
                    # Check for job_search
                    try:
                        present = "job_search" in resolver.reverse_dict
                        f.write(f"\njob_search in reverse_dict: {present}\n")
                        if present:
                            f.write(f"job_search entries: {resolver.reverse_dict.getlist('job_search')!r}\n")
                    except Exception as e:
                        f.write(f"error inspecting job_search: {e}\n")
                print(f"[DIAG] wrote resolver dump to: {fname}")
            except Exception as e:
                print(f"[DIAG] resolver dump failed: {e}")
        return self.get_response(request)
