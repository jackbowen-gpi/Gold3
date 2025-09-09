"""Seed dev data for local development.

Creates a few users, jobs and joblog entries.
Run with: .venv/Scripts/python.exe manage.py runscript seed_dev_data.
"""


def run():
    """Seed development data: create users, jobs and a few items for local testing."""
    from django.contrib.auth.models import User
    from django.contrib.sites.models import Site
    from django.db import transaction
    from django.db.models import signals

    from gchub_db.apps.joblog.models import JobLog

    # Import using the project package paths
    from gchub_db.apps.workflow.models.job import Job, job_post_save, job_pre_save

    print("Seeding dev data...")
    with transaction.atomic():
        # Create users
        users = []
        for u in [
            ("alice", "Alice", "Smith"),
            ("bob", "Bob", "Jones"),
            ("kenton", "Kenton", "Arch"),
        ]:
            user, created = User.objects.get_or_create(
                username=u[0],
                defaults={
                    "first_name": u[1],
                    "last_name": u[2],
                    "email": f"{u[0]}@example.local",
                },
            )
            if created:
                user.set_password("password")
                user.save()
            users.append(user)

        # Ensure a Site exists for workflow.ForeignKey to Site
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "localhost", "name": "Local"}
        )

        # Create jobs (avoid get_or_create because Job.save overrides signature)
        jobs = []
        # Temporarily disable pre_save and post_save processing that expect related items
        try:
            signals.pre_save.disconnect(job_pre_save, sender=Job)
        except Exception:
            pass
        try:
            signals.post_save.disconnect(job_post_save, sender=Job)
        except Exception:
            pass

        for _i, name in enumerate(["Test Job A", "Kenton Plate Job"]):
            job = Job.objects.filter(name=name).first()
            if not job:
                job = Job(name=name, workflow=site)
                # Save without triggering job signals
                job.save()
            jobs.append(job)

        # Reconnect the signals
        try:
            signals.pre_save.connect(job_pre_save, sender=Job)
        except Exception:
            pass
        try:
            signals.post_save.connect(job_post_save, sender=Job)
        except Exception:
            pass

        # Add job logs
        for job in jobs:
            jl = JobLog(
                job=job, user=users[0], type=1, log_text=f"Created job {job.name}"
            )
            jl.save()

    print(
        "Done. Users:",
        User.objects.count(),
        "Jobs:",
        Job.objects.count(),
        "JobLogs:",
        JobLog.objects.count(),
    )

    # Add 30 more jobs and one item each
    print("Adding 30 additional jobs and items...")
    from gchub_db.apps.workflow.models.general import ItemCatalog

    # Ensure there's at least one ItemCatalog for this workflow/site
    catalog = ItemCatalog.objects.filter(workflow=site).first()
    if not catalog:
        catalog = ItemCatalog(size="DEV-SIZE-1", workflow=site)
        catalog.save()

    added_jobs = 0
    # Temporarily disconnect job signals while creating bulk dev jobs/items
    try:
        signals.pre_save.disconnect(job_pre_save, sender=Job)
    except Exception:
        pass
    try:
        signals.post_save.disconnect(job_post_save, sender=Job)
    except Exception:
        pass

    for n in range(30):
        jname = f"DEV JOB {n + 1}"
        j = Job.objects.filter(name=jname).first()
        if not j:
            j = Job(name=jname, workflow=site)
            j.save()
            added_jobs += 1

            # Create a single item for the job
            it = None
            try:
                from gchub_db.apps.workflow.models.item import Item

                it = Item(
                    job=j, workflow=site, size=catalog, bev_item_name=f"Item {n + 1}"
                )
                it.save()
                # Set num_in_job if the manager expects it; attempt to set to 1
                try:
                    it.num_in_job = 1
                    it.save()
                except Exception:
                    pass
            except Exception as e:
                print("Could not create item for job", jname, "error:", e)
    # Reconnect job signals after bulk create
    try:
        signals.pre_save.connect(job_pre_save, sender=Job)
    except Exception:
        pass
    try:
        signals.post_save.connect(job_post_save, sender=Job)
    except Exception:
        pass

    print("Added jobs:", added_jobs)
