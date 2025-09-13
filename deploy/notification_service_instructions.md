Notification daemon deployment guidance

This project uses a small local notification daemon during development to show
Windows toast notifications via `win10toast` and to ensure the notification
library runs on the main thread.

Production considerations

1. Do you need the daemon in production?

   - If your production environment is Windows servers and you want to surface
     server-side OS toasts to a logged-in desktop user, note that server
     environments are typically headless and not appropriate for desktop toasts.
   - For web apps, prefer sending notifications to users using web push, email,
     or application-specific real-time channels rather than OS desktop toasts.

2. Running the daemon as a service (Linux, systemd)

   - Recommended when you deploy an app that needs a local process to deliver
     notifications (e.g., containerized Windows desktop apps are a special case).
   - Example systemd unit (adapt the paths and user):

   ```ini
   [Unit]
   Description=GCHub Notification Daemon
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/srv/gchub_db
   ExecStart=/srv/gchub_db/.venv/bin/python /srv/gchub_db/tools/notification_daemon.py --host 127.0.0.1 --port 5341
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. Running on Windows as a service

   - Use NSSM (Non-Sucking Service Manager) or sc.exe wrappers to run the
     `.venv\Scripts\python.exe` with `tools\notification_daemon.py` arguments.
   - Ensure the service runs under an account that has access to the desktop
     session if desktop toasts are required (this is generally discouraged in
     server environments).

4. Containerized deployments

   - If your app is containerized, consider running the notification logic as
     part of a desktop VM or native process outside containers. Containers don't
     have access to host desktop sessions for toasts.

5. Alternative production approaches

   - Web push + Service Worker for web apps.
   - Platform-specific push services (APNs, FCM) for mobile.
   - In-app toast/alert components rendered in the UI for logged-in users.

Operational notes

- The daemon listens on localhost:5341 by default. Protect it behind localhost
  binding and do not expose it externally.
- Use process supervisors (systemd, Windows Service, supervisord) to keep the
  daemon running and to restart on failures.
- If you modify `tools/notification_daemon.py`, ensure the service unit is
  updated and the service is restarted to pick up changes.
