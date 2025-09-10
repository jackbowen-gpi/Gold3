#!/usr/bin/env python
"""Notification daemon for Windows.

Run this alongside the Django devserver. The daemon exposes a small HTTP
endpoint (/notify) that accepts POST JSON payloads {title,message,duration,icon}
and enqueues them. The daemon's main thread consumes the queue and calls
win10toast.show_toast synchronously, which avoids win10toast main-thread
restrictions when called from Django worker threads.

Usage:
  python tools/notification_daemon.py --host 127.0.0.1 --port 5341
"""

import argparse
import json
import logging
import queue
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

try:
    from win10toast import ToastNotifier

    WIN10TOAST_AVAILABLE = True
except Exception:
    WIN10TOAST_AVAILABLE = False
    logging.warning(
        "win10toast not available in daemon; notifications will print to console"
    )


NOTIFY_QUEUE = queue.Queue()


class NotifyHandler(BaseHTTPRequestHandler):
    def _set_json_response(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_GET(self):
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
            message = payload.get("message") or payload.get("notification", {}).get(
                "message"
            )
            duration = int(payload.get("duration", 10))
            icon = payload.get("icon")
            NOTIFY_QUEUE.put(
                {"title": title, "message": message, "duration": duration, "icon": icon}
            )
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

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )

    server = run_server(args.host, args.port)

    try:
        # Main thread consumes the queue and performs show_toast calls.
        notifier = ToastNotifier() if WIN10TOAST_AVAILABLE else None
        logging.info(
            "Notification consumer started (main thread). WIN10TOAST_AVAILABLE=%s",
            WIN10TOAST_AVAILABLE,
        )
        while True:
            item = NOTIFY_QUEUE.get()
            try:
                title = item.get("title") or "Notification"
                message = item.get("message") or ""
                duration = int(item.get("duration", 10))
                icon = item.get("icon")
                if WIN10TOAST_AVAILABLE and notifier:
                    notifier.show_toast(
                        title,
                        message,
                        duration=min(duration, 60),
                        icon_path=icon,
                        threaded=False,
                    )
                else:
                    logging.info(
                        "NOTIFICATION (daemon fallback): %s - %s", title, message
                    )
            except Exception:
                logging.exception("Error while showing notification")
            finally:
                NOTIFY_QUEUE.task_done()
    except KeyboardInterrupt:
        logging.info("Notification daemon shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
