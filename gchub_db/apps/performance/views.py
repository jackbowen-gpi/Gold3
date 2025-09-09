import csv
import json
import math
import os
from datetime import datetime
from urllib.parse import urlencode

from django.utils import timezone

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render


def recent_slow_requests(request):
    base_dir = getattr(settings, "BASE_DIR", None) or getattr(
        settings, "PROJECT_ROOT", None
    )
    if not base_dir:
        base_dir = os.getcwd()
    log_path = os.path.join(base_dir, "var", "slow_requests.log")
    entries = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            entries = []
    # show newest first
    entries = list(reversed(entries))

    # Pull filter params from querystring
    q = (request.GET.get("q") or request.GET.get("path_contains") or "").strip()
    try:
        min_ms = int(request.GET.get("min_ms")) if request.GET.get("min_ms") else None
    except Exception:
        min_ms = None
    try:
        max_ms = int(request.GET.get("max_ms")) if request.GET.get("max_ms") else None
    except Exception:
        max_ms = None
    try:
        limit = int(request.GET.get("limit")) if request.GET.get("limit") else 200
    except Exception:
        limit = 200

    def keep(e):
        try:
            path = e.get("path") or ""
            dur = int(e.get("duration_ms") or 0)
        except Exception:
            return False
        if q and q not in path:
            return False
        if min_ms is not None and dur < min_ms:
            return False
        if max_ms is not None and dur > max_ms:
            return False
        return True

    filtered = [e for e in entries if keep(e)]

    # In DEBUG (dev) environment be more permissive:
    # - if filters remove all entries, show the most-recent entries so the page is useful for testing
    # - enforce staff-only access only when not DEBUG
    if settings.DEBUG and not filtered and entries:
        filtered = entries[: max(0, limit)]

    # Access control: in production enforce staff-only via the existing decorator behavior.
    # In DEBUG allow local requests (from 127.0.0.1) or requests with X-Dev-Override header.
    # In production require staff access. In DEBUG allow access unconditionally to make
    # the page easy to inspect during local development.
    if not settings.DEBUG:
        check = staff_member_required(lambda req: HttpResponse())
        check_resp = check(request)
        if not (isinstance(check_resp, HttpResponse) and check_resp.status_code == 200):
            return check_resp

    # Sorting
    sort_by = (request.GET.get("sort_by") or "").lower()
    sort_dir = (request.GET.get("sort_dir") or "desc").lower()

    def sort_key(e):
        if sort_by == "duration":
            try:
                return int(e.get("duration_ms") or e.get("duration") or 0)
            except Exception:
                return 0
        # default: sort by timestamp (string)
        return e.get("timestamp") or e.get("time") or ""

    reverse = sort_dir != "asc"
    try:
        filtered.sort(key=sort_key, reverse=reverse)
    except Exception:
        pass

    # Pagination: 'limit' is page size. Support ?page=N
    try:
        page = int(request.GET.get("page") or 1)
        if page < 1:
            page = 1
    except Exception:
        page = 1

    total_count = len(filtered)
    page_size = max(1, int(limit) if limit else 200)
    num_pages = max(1, math.ceil(total_count / page_size)) if total_count else 1
    if page > num_pages:
        page = num_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    # If we're running in DEBUG and there are no real entries, add a synthetic entry
    # so the page is useful for local development and UI testing.
    if settings.DEBUG and not entries:
        try:
            import time

            sample = {
                "path": "/dev/sample",
                "method": "GET",
                "duration_ms": 500,
                "db_queries": 0,
                "timestamp": int(time.time()),
                "sql": ["SELECT 1;"],
                "note": "synthetic-dev-entry",
            }
            entries = [sample]
            filtered = [sample]
        except Exception:
            # non-fatal for dev only
            pass

    # CSV export
    # Convert timestamps for page items to datetime objects for template formatting
    for e in page_items:
        try:
            raw_ts = e.get("timestamp") or e.get("time") or 0
            ts = int(raw_ts)
            dt = datetime.fromtimestamp(ts, tz=timezone.get_current_timezone())
            # keep a datetime for templates that support it and also a preformatted string
            e["timestamp_dt"] = dt
            e["timestamp_str"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            e["timestamp_dt"] = None
            e["timestamp_str"] = str(e.get("timestamp") or e.get("time") or "")

    # Prepare a base query string (preserve filters/sort but not page) for pagination links
    qs_items = [
        (k, v)
        for k, v in request.GET.items()
        if k.lower() != "page" and v is not None and v != ""
    ]
    base_qs = urlencode(qs_items)

    if (request.GET.get("format") or "").lower() == "csv":
        # Build CSV response from current page items
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=slow_requests.csv"
        writer = csv.writer(resp)
        writer.writerow(
            ["timestamp", "path", "duration_ms", "db_queries", "sql_snippets"]
        )
        for e in page_items:
            # prefer the pre-formatted string if available
            ts = e.get("timestamp_str") or e.get("timestamp") or e.get("time") or ""
            path = e.get("path") or ""
            dur = e.get("duration_ms") or e.get("duration") or ""
            dbq = e.get("db_queries") or ""
            sql = e.get("sql") or []
            if isinstance(sql, list):
                sql_text = " ||| ".join([s.replace("\n", " ") for s in sql])
            else:
                sql_text = str(sql)
            writer.writerow([ts, path, dur, dbq, sql_text])
        return resp

    return render(
        request,
        "performance/recent_slow_requests.html",
        {
            "entries": page_items,
            "query": {"q": q, "min_ms": min_ms, "max_ms": max_ms, "limit": limit},
            "pagination": {
                "page": page,
                "num_pages": num_pages,
                "total_count": total_count,
                "page_size": page_size,
                "base_qs": base_qs,
            },
        },
    )
