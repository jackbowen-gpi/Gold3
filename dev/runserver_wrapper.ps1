& 'C:\Dev\Gold\gchub_db\.venv\Scripts\python.exe' 'dev\_dump_db_settings.py' >> 'C:\Dev\Gold\gchub_db\server_stdout.log' 2>&1
& 'C:\Dev\Gold\gchub_db\.venv\Scripts\python.exe' 'dev\_ensure_admin_and_session.py' >> 'C:\Dev\Gold\gchub_db\server_stdout.log' 2>&1
& 'C:\Dev\Gold\gchub_db\.venv\Scripts\python.exe' 'manage.py' 'runserver' '127.0.0.1:8000' '--settings=gchub_db.settings' '--noreload' > 'C:\Dev\Gold\gchub_db\server_stdout.log' 2> 'C:\Dev\Gold\gchub_db\server_stderr.log'
