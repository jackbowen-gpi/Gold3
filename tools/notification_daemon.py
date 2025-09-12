#!/usr/bin/env python
"""
Notification daemon for desktop notifications (cross-platform).

Run this alongside the Django devserver. The daemon exposes a small HTTP
endpoint (/notify) that accepts POST JSON payloads {title,message,duration,icon}
and enqueues them. The daemon's main thread consumes the queue and calls
plyer.notification.notify for cross-platform desktop notifications.

Usage:
    python tools/notification_daemon.py --host 127.0.0.1 --port 5341
"""

import argparse
import json
import logging
import queue
from typing import Dict, Any
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


# Try plyer for cross-platform notifications
try:
    from plyer import notification as plyer_notification  # type: ignore[import-not-found]

    PLYER_AVAILABLE = True
except Exception:
    PLYER_AVAILABLE = False
    logging.warning("plyer not available in daemon; notifications will print to console")


NOTIFY_QUEUE: "queue.Queue[Dict[str, Any]]" = queue.Queue()


class NotifyHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for notification daemon.

    Handles POST requests to /notify to enqueue notifications and GET requests
    to /health for health checks.
    """

    def _set_json_response(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_get(self):
        """
        Handle GET requests for health check endpoint.

        Responds with status 'ok' for '/health', otherwise returns 404.
        """
        if self.path == "/health":
            self._set_json_response(200)
            self.wfile.write(b'{"status":"ok"}')
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/notify":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            # Accept either direct fields or nested 'notification'
            title = payload.get("title") or payload.get("notification", {}).get("title")
            message = payload.get("message") or payload.get("notification", {}).get("message")
            duration = int(payload.get("duration", 10))
            icon = payload.get("icon")
            NOTIFY_QUEUE.put({"title": title, "message": message, "duration": duration, "icon": icon})
            self._set_json_response(200)
            self.wfile.write(b'{"status":"queued"}')
        except Exception as exc:
            logging.exception("Failed to queue notification")
            self._set_json_response(400)
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))


def run_server(host: str, port: int):
    server = ThreadingHTTPServer((host, port), NotifyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logging.info("Notification daemon HTTP server listening on %s:%s", host, port)
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5341)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    server = run_server(args.host, args.port)

    try:
        # Main thread consumes the queue and performs show_toast calls.
        logging.info(
            "Notification consumer started (main thread). PLYER_AVAILABLE=%s",
            PLYER_AVAILABLE,
        )
        while True:
            item: Dict[str, Any] = NOTIFY_QUEUE.get()
            try:
                title = item.get("title") or "Notification"
                message = item.get("message") or ""
                duration = int(item.get("duration", 10))
                icon = item.get("icon")
                if PLYER_AVAILABLE:
                    plyer_notification.notify(
                        title=title,
                        message=message,
                        timeout=min(duration, 60),
                        app_icon=icon,
                        app_name="Gold3 Notification Daemon",
                    )
                else:
                    logging.info("NOTIFICATION (daemon fallback): %s - %s", title, message)
            except Exception:
                logging.exception("Error while showing notification")
            finally:
                NOTIFY_QUEUE.task_done()
    except KeyboardInterrupt:
        logging.info("Notification daemon shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
