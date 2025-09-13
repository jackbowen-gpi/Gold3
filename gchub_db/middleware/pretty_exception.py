"""
Middleware that logs a concise, nicely formatted exception summary for dev.

This middleware is intended for use in DEBUG/dev only. It logs the exception
type, message and a short stack trace (last few frames) to the standard logging
system so the console output is easier to read during development.
"""

import logging
import traceback

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("pretty_exceptions")


class PrettyExceptionMiddleware(MiddlewareMixin):
    """
    Catch unhandled exceptions and emit a concise formatted log entry.

    Django's debug page is still shown when DEBUG=True. This middleware only
    improves the log output so terminal/CI logs are easier to scan.
    """

    def process_exception(self, request, exception):
        try:
            tb = traceback.TracebackException.from_exception(exception)
            # Render just the last few stack frames to keep console output concise
            frames = list(tb.stack)[-6:]
            summary_lines = [f"Exception: {tb.exc_type.__name__}: {tb}"]
            summary_lines.append("Trace (most recent frames):")
            for f in frames:
                summary_lines.append(f"  {f.filename}:{f.lineno} in {f.name}")
            # Include the full formatted exception at debug level
            logger.error("\n" + "\n".join(summary_lines))
            logger.debug("Full traceback:\n" + "".join(tb.format()))
        except Exception:
            logger.exception("Failed to format exception")
        # Returning None lets Django continue to handle the response (500/debug page)
        return None
