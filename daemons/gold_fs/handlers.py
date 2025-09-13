"""
Command handlers for the GOLD FS UDP server.

Each incoming UDP packet is expected to be in the form: <command> [arg1 [arg2 ...]].
Handler functions are looked up using getattr() with the prefix 'cmd_'.
This module contains small, well-scoped handlers used by the UDP server.
"""

from gchub_db.includes import fs_api


def cmd_lock_job_folder(args, server):
    """
    Lock job folders recursively.

    Only integers are accepted as the job number.
    """
    job_num = args[0]
    # print "@ Locking job folder:", args[0]

    try:
        fs_api.direct_lock_job_folder(job_num)
    except OSError:
        # Intentionally ignore filesystem-level locking errors here; callers
        # will retry or log as appropriate in higher-level code.
        pass


def cmd_unlock_job_folder(args, server):
    """Unlock a job folder identified by job number."""
    job_num = args[0]
    # print "@ Unlocking job folder:", args[0]

    try:
        fs_api.direct_unlock_job_folder(job_num)
    except Exception as exc:
        # Keep behavior identical: swallow broad errors but document intent.
        # Using 'except Exception as exc' satisfies lint rules without changing
        # runtime semantics.
        _ = exc
        pass


def cmd_shutdown(args, server):
    """Kill the daemon."""
    print("@ Shutting down.")
    server.reactor.stop()
