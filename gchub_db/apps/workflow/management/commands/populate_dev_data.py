from __future__ import annotations

import datetime
import os
import random
import uuid
from decimal import Decimal
from typing import Any, Dict

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import IntegrityError, connection, transaction
from django.db.models.fields import NOT_PROVIDED
from django.utils import timezone

DEFAULT_COUNT = int(os.environ.get("POPULATE_DEFAULT_COUNT", "5"))


class Command(BaseCommand):
    help = "Populate the dev DB with minimal sample rows (dry-run by default)."

    def add_arguments(self, parser):
        """CLI arguments for the command."""
        parser.add_argument(
            "--count",
            type=int,
            default=DEFAULT_COUNT,
            help=(
                f"How many rows to create per model (default {DEFAULT_COUNT}). Override with POPULATE_DEFAULT_COUNT env or --count."
            ),
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Actually save changes to the database (default: dry-run)",
        )
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="Only populate models that currently have zero rows",
        )
        parser.add_argument(
            "--curated",
            action="store_true",
            help="Create a small curated, coherent dataset for core workflow models",
        )
        parser.add_argument(
            "--apps",
            type=str,
            help=("Comma-separated app labels to limit population to, e.g. workflow,auth"),
        )
        parser.add_argument(
            "--models",
            type=str,
            help=("Comma-separated model labels to limit population to, e.g. workflow.Item,auth.User"),
        )

    def handle(self, *args, **options):
        """Main entrypoint for the command."""
        count = options["count"]
        do_commit = options["commit"]
        only_empty = options["only_empty"]
        curated = options.get("curated", False)
        apps_filter = options.get("apps")
        models_filter = options.get("models")

        self.stdout.write("Starting dev DB population (dry-run = %s)" % (do_commit and "NO" or "YES"))

        # collect models and apply optional filters
        all_models = list(apps.get_models())
        if apps_filter:
            wanted = {a.strip() for a in apps_filter.split(",") if a.strip()}
            all_models = [m for m in all_models if m._meta.app_label in wanted]
        if models_filter:
            wanted = {s.strip() for s in models_filter.split(",") if s.strip()}

            def label_of(m):
                return f"{m._meta.app_label}.{m._meta.object_name}"

            all_models = [m for m in all_models if label_of(m) in wanted]

        created_summary = []

        # curated mode: create a small coherent set first, then continue
        # generic population
        if curated:
            self.stdout.write("Running curated/core seeder first...")
            try:
                self._seed_curated(count, do_commit)
            except Exception as exc:
                self.stderr.write(f"Curated seeder failed: {exc}")
            else:
                # after curated seeding, prefer to only populate empty models to
                # avoid duplicate/unique errors
                only_empty = True
                self.stdout.write("Curated seeder finished: will only populate empty models in generic pass.")

        for model in all_models:
            # skip unmanaged or proxy models
            opts = getattr(model, "_meta")
            if not opts.managed or opts.proxy:
                continue

            # skip django internal models that the seeder shouldn't create
            if opts.app_label in ("contenttypes", "auth") and opts.object_name in (
                "ContentType",
                "Permission",
            ):
                self.stdout.write(f"Skipping internal model {opts.app_label}.{opts.object_name}")
                continue
            # skip admin_log models in the generic pass; AdminLog is special-cased
            if opts.object_name == "AdminLog" or opts.app_label == "admin_log":
                self.stdout.write(f"Skipping admin app model {opts.app_label}.{opts.object_name} (handled separately)")
                continue

            try:
                existing = model.objects.count()
            except Exception as e:
                # some models may not be queryable in certain DB states; attempt a
                # lightweight raw-check to see if the underlying table exists and
                # has any rows (helps when migrations/tables are partially present).
                try:
                    table = getattr(model._meta, "db_table", None) or model._meta.label_lower
                    with connection.cursor() as cur:
                        cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
                        row = cur.fetchone()
                    existing = 1 if row else 0
                except Exception as e2:
                    # still failing: surface the original error and skip model
                    self.stderr.write(f"Skipping model (count failed): {model.__module__}.{model.__name__} -- {e}")
                    self.stderr.write(f"Fallback check failed: {e2}")
                    continue

            if only_empty and existing > 0:
                self.stdout.write(f"Skipping {model.__name__} (has {existing} rows)")
                continue

            to_create = count
            created = 0
            for i in range(to_create):
                # build kwargs for minimal create
                kwargs: Dict[str, Any] = {}
                m2m_fields = []
                missing_required_fk = False
                for field in opts.get_fields():
                    # skip reverse relations and m2m placeholder (handle after save)
                    if field.auto_created and not getattr(field, "concrete", False):
                        continue
                    if getattr(field, "many_to_many", False):
                        m2m_fields.append(field)
                        continue
                    # skip auto PKs
                    if getattr(field, "auto_created", False) and getattr(field, "primary_key", False):
                        continue

                    fname = field.name
                    if getattr(field, "primary_key", False) and getattr(field, "auto_created", False):
                        continue

                    # do not unconditionally skip non-editable fields: if the field is a
                    # relationship (ForeignKey/OneToOne) we still want to attempt to
                    # populate it even when editable=False (admin-only flag).
                    if getattr(field, "editable", True) is False and not (
                        getattr(field, "many_to_one", False) or getattr(field, "one_to_one", False)
                    ):
                        continue

                    # handle relationships
                    if field.many_to_one or field.one_to_one:
                        rel_model = field.related_model
                        try:
                            rel_instance = rel_model.objects.first()
                        except Exception:
                            rel_instance = None
                        if not rel_instance:
                            # create one for the related model (recursively shallow)
                            rel_instance = self._create_minimal_instance(rel_model)
                            if rel_instance is None:
                                # if the FK is nullable, we can set None; otherwise
                                # we must skip creating this model
                                if getattr(field, "null", False):
                                    kwargs[fname] = None
                                    continue
                                else:
                                    missing_required_fk = True
                                    break
                        kwargs[fname] = rel_instance
                        continue

                    # basic field types
                    internal_type = getattr(field, "get_internal_type", lambda: "").__call__()
                    if internal_type in ("CharField", "TextField"):
                        # generate plausibly-typed strings based on the field name
                        val = self._make_string_for_field(model.__name__, fname, i, field)
                        # keep unique fields unique
                        if getattr(field, "unique", False):
                            val = f"{val}_{uuid.uuid4().hex[:6]}"
                        kwargs[fname] = val[: (field.max_length or 60)] if getattr(field, "max_length", None) else val
                    elif internal_type in (
                        "IntegerField",
                        "PositiveIntegerField",
                        "PositiveSmallIntegerField",
                        "SmallIntegerField",
                        "BigIntegerField",
                    ):
                        kwargs[fname] = self._make_int_for_field(fname)
                    elif internal_type in ("AutoField", "BigAutoField"):
                        # skip auto-generated PKs
                        continue
                    elif internal_type in ("BooleanField", "NullBooleanField"):
                        # random but stable-ish
                        kwargs[fname] = random.choice((True, False))
                    elif internal_type in ("DateField",):
                        kwargs[fname] = timezone.now().date() + datetime.timedelta(days=random.randint(-30, 30))
                    elif internal_type in ("DateTimeField",):
                        kwargs[fname] = timezone.now() + datetime.timedelta(hours=random.randint(-200, 200))
                    elif internal_type in ("DecimalField", "FloatField"):
                        # generate a small decimal value
                        kwargs[fname] = Decimal(str(round(random.uniform(0.5, 100.0), 2)))
                    elif internal_type in ("UUIDField",):
                        kwargs[fname] = uuid.uuid4()
                    elif internal_type in ("JSONField",):
                        kwargs[fname] = {}
                    else:
                        # fallback for unknown field types: try default or None
                        # or a simple string
                        # only honor explicit defaults that are real values
                        # (not the NOT_PROVIDED sentinel)
                        if getattr(field, "default", None) is not None and getattr(field, "default") is not NOT_PROVIDED:
                            try:
                                kwargs[fname] = field.default() if callable(field.default) else field.default
                                continue
                            except Exception:
                                pass
                        if getattr(field, "null", False):
                            kwargs[fname] = None
                        else:
                            kwargs[fname] = f"{model.__name__}_{i}_{fname}"

                # skip creating this model if a required FK was not resolvable
                if missing_required_fk:
                    self.stderr.write(f"Skipping {opts.object_name} creation: required FK not available")
                    continue

                # create instance (dry-run unless commit)
                # Special-case: avoid generically creating queue/aux models that require
                # a persisted Item if none is available. These models are created by
                # dedicated factories or by item methods; generic creation often fails
                # with NOT NULL constraints when the Item cannot be resolved.
                try:
                    if model._meta.app_label == "queues" and model.__name__ in (
                        "ColorKeyQueue",
                        "TiffToPDF",
                    ):
                        item_model = apps.get_model("workflow", "Item") if apps.is_installed("workflow") else None
                        has_item = False
                        if item_model:
                            try:
                                it = item_model.objects.first()
                                if it and getattr(it, "pk", None):
                                    has_item = True
                                else:
                                    # try to create a minimal persisted item
                                    it = self._create_minimal_instance(item_model)
                                    if it and getattr(it, "pk", None):
                                        has_item = True
                            except Exception:
                                has_item = False
                    if not has_item:
                        self.stderr.write(f"Skipping {model.__name__} creation: no persisted Item available (generic pass)")
                        continue
                    else:
                        # TEMP DIAGNOSTIC: log the item that will be used for
                        # generic queue creation
                        try:
                            itrepr = repr(it)
                        except Exception:
                            itrepr = "<repr-failed>"
                        # split to avoid overly long source line
                        self.stderr.write(f"[DIAG][generic-queue] will use item={itrepr}")
                        self.stderr.write(f"pk={getattr(it, 'pk', None)}")
                except Exception:
                    pass

                if do_commit:
                    try:
                        with transaction.atomic():
                            # If there are unique fields, prefer get_or_create
                            # to avoid IntegrityError
                            unique_lookup = {}
                            try:
                                for f in opts.fields:
                                    if getattr(f, "unique", False) and f.name in kwargs:
                                        unique_lookup[f.name] = kwargs[f.name]
                            except Exception:
                                unique_lookup = {}

                            if unique_lookup:
                                try:
                                    # strip NOT_PROVIDED sentinel values from
                                    # defaults to avoid attribute errors
                                    safe_defaults = {k: v for k, v in kwargs.items() if v is not NOT_PROVIDED}
                                    # ensure any model instances in
                                    # safe_defaults are persisted
                                    for k, v in list(safe_defaults.items()):
                                        try:
                                            from django.db.models import Model

                                            if isinstance(v, Model):
                                                if getattr(v, "pk", None) is None:
                                                    try:
                                                        v.save()
                                                    except Exception:
                                                        # try to get/create a persisted
                                                        # fallback instance
                                                        try:
                                                            fallback = self._create_minimal_instance(type(v))
                                                            if fallback and getattr(fallback, "pk", None):
                                                                safe_defaults[k] = fallback
                                                            else:
                                                                del safe_defaults[k]
                                                        except Exception:
                                                            # can't persist
                                                            # drop key
                                                            # avoid unsaved
                                                            # instance
                                                            del safe_defaults[k]
                                                    # if the field is required, we'll
                                                    # fall back later
                                        except Exception:
                                            continue
                                    obj, was_created = model.objects.get_or_create(**unique_lookup, defaults=safe_defaults)
                                    self.stdout.write((f"Used get_or_create for {model.__name__} lookup={unique_lookup}"))
                                    inst = obj
                                    if was_created:
                                        # ensure m2m relations are set for
                                        # newly created object
                                        for m2m in m2m_fields:
                                            try:
                                                rel_model = m2m.related_model
                                                rel = rel_model.objects.first()
                                                if not rel:
                                                    rel = self._create_minimal_instance(rel_model)
                                                if rel:
                                                    getattr(inst, m2m.name).add(rel)
                                            except Exception:
                                                continue
                                        created += 1
                                    else:
                                        # already existed, count as skip
                                        pass
                                except Exception:
                                    # fallback to normal save path below
                                    # sanitize kwargs: remove NOT_PROVIDED
                                    # sentinel values
                                    safe_kwargs = {k: v for k, v in kwargs.items() if v is not NOT_PROVIDED}
                                    # ensure FK instances are persisted or
                                    # else skip creating this model
                                    skip_due_to_unsaved_fk = False
                                    for k, v in list(safe_kwargs.items()):
                                        try:
                                            from django.db.models import Model

                                            if isinstance(v, Model) and getattr(v, "pk", None) is None:
                                                try:
                                                    v.save()
                                                except Exception:
                                                    skip_due_to_unsaved_fk = True
                                                    break
                                        except Exception:
                                            continue
                                    if skip_due_to_unsaved_fk:
                                        self.stderr.write(f"Skipping {model.__name__} creation: related FK could not be persisted")
                                        continue
                                    inst = model(**safe_kwargs)
                                    try:
                                        inst.save()
                                    except TypeError:
                                        inst.save()
                                    for m2m in m2m_fields:
                                        try:
                                            rel_model = m2m.related_model
                                            rel = rel_model.objects.first()
                                            if not rel:
                                                rel = self._create_minimal_instance(rel_model)
                                            if rel:
                                                getattr(inst, m2m.name).add(rel)
                                        except Exception:
                                            continue
                                    created += 1
                            else:
                                # avoid QuerySet.create() because it may call
                                # save(force_insert=True) on models that override
                                # save() without **kwargs; sanitize and instantiate
                                # and save()
                                safe_kwargs = {k: v for k, v in kwargs.items() if v is not NOT_PROVIDED}
                                # Ensure FK instances are persisted, or attempt to
                                # replace them with persisted minimal instances
                                skip_due_to_unsaved_fk = False
                                for k, v in list(safe_kwargs.items()):
                                    try:
                                        from django.db.models import Model

                                        if isinstance(v, Model) and getattr(v, "pk", None) is None:
                                            try:
                                                v.save()
                                            except Exception:
                                                # attempt to create/obtain a minimal
                                                # persisted instance for this related
                                                # model
                                                try:
                                                    fallback = self._create_minimal_instance(type(v))
                                                    if fallback and getattr(fallback, "pk", None):
                                                        safe_kwargs[k] = fallback
                                                        continue
                                                except Exception:
                                                    pass
                                                skip_due_to_unsaved_fk = True
                                                break
                                    except Exception:
                                        continue
                                if skip_due_to_unsaved_fk:
                                    self.stderr.write((f"Skipping {model.__name__} creation: related FK could not be persisted"))
                                    continue
                                inst = model(**safe_kwargs)
                                try:
                                    inst.save()
                                except TypeError:
                                    # fallback: try calling save without any kwargs
                                    inst.save()

                                # set m2m relations if any
                                for m2m in m2m_fields:
                                    try:
                                        rel_model = m2m.related_model
                                        rel = rel_model.objects.first()
                                        if not rel:
                                            rel = self._create_minimal_instance(rel_model)
                                        if rel:
                                            getattr(inst, m2m.name).add(rel)
                                    except Exception:
                                        continue
                                created += 1
                    except IntegrityError as ie:
                        # try to detect an existing row and skip, otherwise log
                        try:
                            # attempt a best-effort lookup using unique fields
                            unique_lookup = {}
                            for f in opts.fields:
                                if getattr(f, "unique", False) and f.name in kwargs:
                                    unique_lookup[f.name] = kwargs[f.name]
                            if unique_lookup and model.objects.filter(**unique_lookup).exists():
                                # already exists, skip
                                continue
                        except Exception:
                            pass
                        self.stderr.write(f"IntegrityError creating {model.__name__}: {ie}")
                        continue
                    except Exception as exc:
                        self.stderr.write(f"Error creating {model.__name__}: {exc}")
                        continue
                else:
                    # dry-run: just report what we would create. Use a safe repr
                    # to avoid __str__ side-effects
                    safe = self._safe_kwargs(kwargs)
                    self.stdout.write(f"DRYRUN: would create {model.__name__} with: {safe}")
                    created += 1

            if created:
                created_summary.append((model.__name__, created, existing))

        # summary
        self.stdout.write("\nPopulation summary:")
        for name, added, existed in created_summary:
            self.stdout.write(f"Model {name}: existed={existed} added={added}")

        if not do_commit:
            self.stdout.write(("\nDry-run mode: no changes were written. Re-run with --commit to persist data."))

    def _create_minimal_instance(self, model, _depth=0):
        """
        Create a minimal instance for `model` (used for FK/M2M targets).
        Returns the created instance or None on failure.
        Depth prevents infinite recursion.
        """
        if _depth > 4:
            return None
        # avoid creating ContentType / Permission rows which have strict uniqueness and
        # are managed by Django; let existing ones be used instead.
        try:
            if model._meta.app_label == "contenttypes" and model._meta.object_name == "ContentType":
                return None
            if model._meta.app_label == "auth" and model._meta.object_name == "Permission":
                return None
        except Exception:
            pass

        try:
            if model.objects.exists():
                return model.objects.first()
        except Exception:
            return None

        opts = getattr(model, "_meta")
        kwargs = {}
        m2m_fields = []
        for field in opts.get_fields():
            if field.auto_created and not getattr(field, "concrete", False):
                continue
            if getattr(field, "many_to_many", False):
                m2m_fields.append(field)
                continue
            if getattr(field, "auto_created", False) and getattr(field, "primary_key", False):
                continue
            # similar to the generic path, allow non-editable relationship fields
            # to be considered when creating minimal instances, because many
            # models mark FKs editable=False but still require them at DB level.
            if getattr(field, "editable", True) is False and not (
                getattr(field, "many_to_one", False) or getattr(field, "one_to_one", False)
            ):
                continue

            if field.many_to_one or field.one_to_one:
                rel_model = field.related_model
                rel_instance = self._create_minimal_instance(rel_model, _depth=_depth + 1)
                if rel_instance is None:
                    continue
                kwargs[field.name] = rel_instance
                continue

            internal_type = getattr(field, "get_internal_type", lambda: "").__call__()
            if internal_type in ("CharField", "TextField"):
                base = f"{model.__name__}_example_{field.name}"
                kwargs[field.name] = base[: (field.max_length or 60)] if getattr(field, "max_length", None) else base
            elif internal_type in (
                "IntegerField",
                "PositiveIntegerField",
                "SmallIntegerField",
                "BigIntegerField",
            ):
                kwargs[field.name] = 1
            elif internal_type in ("BooleanField", "NullBooleanField"):
                kwargs[field.name] = False
            elif internal_type in ("DateField",):
                kwargs[field.name] = timezone.now().date()
            elif internal_type in ("DateTimeField",):
                kwargs[field.name] = timezone.now()
            elif internal_type in ("DecimalField", "FloatField"):
                kwargs[field.name] = Decimal("1.0")
            elif internal_type in ("UUIDField",):
                kwargs[field.name] = uuid.uuid4()
            else:
                if getattr(field, "null", False):
                    kwargs[field.name] = None
                else:
                    kwargs[field.name] = f"{model.__name__}_{field.name}"

        # try to honor defaults and choices
        for f in opts.fields:
            if f.name in kwargs:
                continue
            try:
                # avoid assigning the NOT_PROVIDED sentinel into kwargs
                if getattr(f, "default", None) is not None and f.default is not NOT_PROVIDED and f.default is not None:
                    kwargs[f.name] = f.default() if callable(f.default) else f.default
                    continue
                if getattr(f, "choices", None):
                    # pick the first choice value
                    kwargs[f.name] = f.choices[0][0]
                    continue
            except Exception:
                pass

        try:
            with transaction.atomic():
                inst = model(**kwargs)
                try:
                    inst.save()
                except TypeError:
                    inst.save()
                for m2m in m2m_fields:
                    try:
                        rel_model = m2m.related_model
                        rel = rel_model.objects.first()
                        if not rel:
                            rel = self._create_minimal_instance(rel_model, _depth=_depth + 1)
                        if rel:
                            getattr(inst, m2m.name).add(rel)
                    except Exception:
                        continue
                return inst
        except Exception:
            return None

    # Curated seeding helpers + per-model factory overrides
    def _seed_curated(self, count: int, do_commit: bool):
        """
        Seed a small, coherent dataset for core developer workflows.

        This creates users, then creates a small set of 'item' and 'job'-like records
        if those models exist in the `workflow` app. It is intentionally conservative
        and will only create models that are present.
        """
        # create some base users first
        users = self._create_users(count, do_commit)

        # ensure a Site exists for workflow-related factories
        # and cache it
        try:
            SiteModel = apps.get_model("sites", "Site") if apps.is_installed("sites") else None
            curated_site = None
            if SiteModel:
                if do_commit:
                    try:
                        curated_site, _ = SiteModel.objects.get_or_create(domain="dev.local", defaults={"name": "DevWorkflow"})
                    except Exception:
                        # fallback to first existing or minimal instance
                        curated_site = SiteModel.objects.first() or self._create_minimal_instance(SiteModel)
                else:
                    # Dry-run: prefer an existing Site. Otherwise create a
                    # minimal instance in memory for simulation.
                    curated_site = SiteModel.objects.first() or self._create_minimal_instance(SiteModel)
            # store for factories to reuse (may be None)
            self._curated_site = curated_site
        except Exception:
            self._curated_site = None

        # attempt to create workflow app models in a sensible order
        try:
            app_cfg = apps.get_app_config("workflow")
            workflow_models = list(app_cfg.get_models())
        except Exception:
            workflow_models = []

        # Run Job factory first (many other models depend on Job/Item existing)
        # collect created Job instances so other factories can reference them
        self._curated_jobs = []
        job_factory = getattr(self, "_factory__job", None)
        if callable(job_factory):
            self.stdout.write("Curated: running factory for workflow.Job (first)")
            try:
                for i in range(count):
                    inst = job_factory(i, do_commit, users)
                    if inst is not None:
                        self._curated_jobs.append(inst)
            except Exception as exc:
                self.stderr.write(f"Factory error for workflow.Job: {exc}")

        # try per-model factory overrides for remaining models
        for model in workflow_models:
            # skip Job because we already ran it
            if getattr(model, "_meta", None) and model._meta.object_name == "Job":
                continue
            label = f"{model._meta.app_label}.{model._meta.object_name}"
            factory = getattr(
                self,
                f"_factory__{model._meta.object_name.lower()}",
                None,
            )
            if callable(factory):
                self.stdout.write(f"Curated: running factory for {label}")
                try:
                    for i in range(count):
                        factory(i, do_commit, users)
                except Exception as exc:
                    self.stderr.write(f"Factory error for {label}: {exc}")

        # Fallback: ensure there's at least `count` rows for models that look
        # like items/jobs. We look for models with a 'name' or 'title' field
        # and create instances via existing logic.
        for model in workflow_models:
            opts = model._meta
            field_names = {f.name for f in opts.fields}
            if not ("name" in field_names or "title" in field_names):
                continue
            existing = 0
            try:
                existing = model.objects.count()
            except Exception:
                continue
            to_create = max(0, count - existing)
            if to_create <= 0:
                continue
            self.stdout.write(f"Curated: ensuring {to_create} instances of {model._meta.label}")
            for i in range(to_create):
                # delegate to generic path but try to satisfy fks with users/items
                kwargs = {}
                for f in opts.fields:
                    if getattr(f, "auto_created", False) and getattr(f, "primary_key", False):
                        continue
                    if not getattr(f, "editable", True):
                        continue
                    internal = getattr(f, "get_internal_type", lambda: "")()
                    if internal in ("CharField", "TextField") and f.name in (
                        "name",
                        "title",
                    ):
                        kwargs[f.name] = f"{model._meta.object_name}_{i}"
                    elif f.many_to_one or f.one_to_one:
                        rel_model = f.related_model
                        # prefer user or first existing
                        if rel_model._meta.label == "auth.User" and users:
                            kwargs[f.name] = users[0]
                        else:
                            rel = rel_model.objects.first() or self._create_minimal_instance(rel_model)
                            if rel:
                                kwargs[f.name] = rel
                    elif internal in ("IntegerField", "PositiveIntegerField"):
                        kwargs[f.name] = 1
                    elif internal in ("UUIDField",):
                        kwargs[f.name] = uuid.uuid4()
                    elif getattr(f, "null", False):
                        kwargs[f.name] = None
                if do_commit:
                    try:
                        inst = model(**kwargs)
                        inst.save()
                    except Exception:
                        continue
                    else:
                        # Dry-run: report what would be created without persisting.
                        self.stdout.write((f"DRYRUN curated: would create {model._meta.label} with {kwargs}"))

        # Ensure at least one instance per workflow/site for models that
        # include a workflow FK. This makes sure every Site/workflow has
        # an example Job and related workflow-scoped records.
        try:
            site_model = apps.get_model("sites", "Site") if apps.is_installed("sites") else None
            if site_model:
                sites = (
                    list(site_model.objects.all())
                    if do_commit
                    else ([getattr(self, "_curated_site", None)] if getattr(self, "_curated_site", None) else [])
                )
                if sites:
                    # Notify that we will ensure at least one instance per
                    # workflow/site for workflow-scoped models
                    self.stdout.write(("Curated: ensuring at least one per workflow/site for workflow-scoped models"))
                    for model in workflow_models:
                        opts = model._meta
                        # find a field that points to Site (workflow FK)
                        workflow_field = None
                        for f in opts.fields:
                            try:
                                if getattr(f, "related_model", None) is site_model or f.name == "workflow":
                                    workflow_field = f
                                    break
                            except Exception:
                                continue
                        if not workflow_field:
                            continue

                        for site in sites:
                            try:
                                qs = model.objects.filter(**{workflow_field.name: site})
                                if qs.exists():
                                    continue
                            except Exception:
                                # Could not query; skip
                                continue

                            # Need to create one for this site
                            if do_commit:
                                factory = getattr(self, f"_factory__{opts.object_name.lower()}", None)
                                inst = None
                                if callable(factory):
                                    try:
                                        inst = factory(0, True, users)
                                    except Exception:
                                        inst = None

                                if inst is None:
                                    # try create minimal instance and attach the site
                                    inst = self._create_minimal_instance(model)
                                    if inst:
                                        try:
                                            setattr(inst, workflow_field.name, site)
                                            inst.save()
                                        except Exception:
                                            # fallback: attempt direct instantiation
                                            # with minimal data
                                            try:
                                                data = {workflow_field.name: site}
                                                field_names = {f.name for f in opts.fields}
                                                if "name" in field_names:
                                                    # short site name retrieval
                                                    site_name = getattr(site, "name", site)
                                                    data["name"] = f"{opts.object_name}_for_{site_name}"
                                                inst = model(**data)
                                                inst.save()
                                            except Exception as exc:
                                                site_name = getattr(site, "name", site)
                                                label = opts.label
                                                msg = f"Curated: failed create {label} for site {site_name}: {exc}"
                                                self.stderr.write(msg)
                                                inst = None

                                if inst:
                                    try:
                                        msg = f"Curated: created {opts.label} for site={site_name} pk={getattr(inst, 'pk', None)}"
                                        self.stdout.write(msg)
                                    except Exception:
                                        pass
                            else:
                                # Dry-run: report which curated instance would be
                                # created
                                try:
                                    msg = f"DRYRUN curated: would create {opts.label} for site={getattr(site, 'name', site)}"
                                    self.stdout.write(msg)
                                except Exception:
                                    pass
        except Exception:
            pass

    def _create_users(self, count: int, do_commit: bool):
        users = []
        try:
            User = apps.get_model("auth", "User")
        except Exception:
            return users

        for i in range(count):
            username = f"devuser{i}"
            email = f"devuser{i}@example.com"
            if do_commit:
                try:
                    # instantiate and save to avoid manager.create() passing
                    # force_insert kwargs
                    u = User(username=username, email=email)
                    try:
                        u.set_password("password")
                    except Exception:
                        pass
                    try:
                        u.save()
                    except TypeError:
                        u.save()
                    users.append(u)
                except IntegrityError:
                    u = User.objects.filter(username=username).first() or User.objects.first()
                    if u:
                        users.append(u)
                except Exception:
                    continue
            else:
                self.stdout.write(f"DRYRUN curated: would create User {username}")
        return users

    # Example per-model factories. Add more by creating methods named
    # _factory__<ModelName>
    def _factory__job(self, index: int, do_commit: bool, users: list):
        """
        Factory for a Job-like model: set a name/title and link to a
        dev user if possible.
        """
        try:
            model = apps.get_model("workflow", "Job")
        except Exception:
            return
        # create a minimal Job: only set name and workflow to avoid
        # save-time relation access
        kwargs = {"name": f"Job_{index}"}
        # Resolve workflow FK dynamically (some installs don't declare 'sites' app)
        try:
            try:
                workflow_field = model._meta.get_field("workflow")
                RelModel = workflow_field.related_model
            except Exception:
                RelModel = None
            site = None
            if RelModel:
                try:
                    site = RelModel.objects.first()
                except Exception:
                    site = None
                if site is None:
                    try:
                        # avoid manager.create to prevent save() kwargs issues
                        candidate = RelModel(name="DevSite", domain="example.com")
                        try:
                            candidate.save()
                        except TypeError:
                            candidate.save()
                        site = candidate
                    except Exception:
                        site = self._create_minimal_instance(RelModel)
            if site:
                kwargs["workflow"] = site
        except Exception:
            pass

        if do_commit:
            try:
                # Temporarily disconnect job signals to avoid pre_save
                # accessing related sets
                try:
                    from django.db.models import signals

                    from gchub_db.apps.workflow.models.job import (
                        job_post_save,
                        job_pre_save,
                    )

                    try:
                        signals.pre_save.disconnect(job_pre_save, sender=model)
                    except Exception:
                        pass
                    try:
                        signals.post_save.disconnect(job_post_save, sender=model)
                    except Exception:
                        pass
                except Exception:
                    # if we can't import or disconnect, continue and try create anyway
                    pass

                # prefer direct manager create to ensure PK is assigned
                # before any relation access
                try:
                    # Instantiate and call save() directly to avoid passing
                    # unwanted kwargs like `force_insert` through managers.
                    inst = model(**{k: v for k, v in kwargs.items() if v is not None})
                    try:
                        inst.save()
                    except TypeError:
                        # some models override save() without kwargs; call without args
                        inst.save()
                    # explicit log after save
                    try:
                        msg = f"Created Job pk={getattr(inst, 'pk', None)} name={getattr(inst, 'name', None)}"
                        self.stdout.write(msg)
                    except Exception:
                        pass
                except Exception:
                    # If creation failed, log a generic message (exc not available here)
                    self.stderr.write("Error creating curated Job")
            finally:
                # Reconnect signals if we disconnected them
                try:
                    from django.db.models import signals

                    from gchub_db.apps.workflow.models.job import (
                        job_post_save,
                        job_pre_save,
                    )

                    try:
                        signals.pre_save.connect(job_pre_save, sender=model)
                    except Exception:
                        pass
                    try:
                        signals.post_save.connect(job_post_save, sender=model)
                    except Exception:
                        pass
                except Exception:
                    pass
            # return the created instance so callers can reference it (verify PK)
            try:
                if inst and getattr(inst, "pk", None):
                    return inst
                else:
                    return None
            except Exception:
                return None
        else:
            self.stdout.write(f"DRYRUN curated: would create Job with {self._safe_kwargs(kwargs)}")
            return None

    def _factory__item(self, index: int, do_commit: bool, users: list):
        """Factory for an Item-like model (common pattern in workflow apps)."""
        # try some common item model names
        for name in ("Item", "ItemCatalog", "ItemSpec"):
            try:
                model = apps.get_model("workflow", name)
            except Exception:
                continue

            kwargs = {}
            # First, ensure any FK to Job is assigned from curated jobs so we
            # don't create orphaned Items during the curated pass. Do a
            # pre-pass over fields to set required relation fields.
            # This avoids passing unexpected kwargs like `force_insert`
            # through the manager layer which can cause errors.
            for f in model._meta.fields:
                if getattr(f, "auto_created", False) and getattr(f, "primary_key", False):
                    continue
                if not getattr(f, "editable", True):
                    continue

                # handle relationship fields first
                if f.many_to_one or f.one_to_one:
                    rel_model = getattr(f, "related_model", None)
                    if rel_model and getattr(rel_model._meta, "object_name", "") == "Job":
                        # prefer curated job instances
                        curated = [j for j in getattr(self, "_curated_jobs", []) if j and getattr(j, "pk", None)]
                        if curated:
                            kwargs[f.name] = curated[0]
                            continue
                        else:
                            # No curated job available — cannot safely create
                            # this Item without a curated Job FK
                            kwargs = None
                            break
                    # For non-Job foreign keys: try to use an existing instance
                    # or create a minimal one so related constraints are satisfied
                    try:
                        rel = rel_model.objects.first() if rel_model else None
                    except Exception:
                        rel = None
                    if not rel and rel_model:
                        rel = self._create_minimal_instance(rel_model)
                    if rel:
                        kwargs[f.name] = rel
                    elif getattr(f, "null", False):
                        kwargs[f.name] = None
                    else:
                        # required FK missing and cannot create it
                        kwargs = None
                        break

            if kwargs is None:
                # required FK missing (e.g. no Job); skip creating this item
                if do_commit:
                    self.stderr.write((f"Skipping curated {model._meta.object_name}: required FK not available"))
                else:
                    self.stdout.write((f"DRYRUN curated: would skip {model._meta.object_name} (no Job available)"))
                return

            # Second pass: fill in simple fields like name/title and basic scalars
            for f in model._meta.fields:
                if getattr(f, "auto_created", False) and getattr(f, "primary_key", False):
                    continue
                if not getattr(f, "editable", True):
                    continue
                if f.name in kwargs:
                    # already set (FKs)
                    continue
                if f.name in ("name", "title"):
                    kwargs[f.name] = f"Item_{index}"
                elif getattr(f, "null", False):
                    kwargs[f.name] = None
                elif getattr(f, "get_internal_type", lambda: "")() in ("IntegerField",):
                    kwargs[f.name] = 1

            if do_commit:
                try:
                    inst = model(**kwargs)
                    inst.save()
                    try:
                        self.stdout.write((f"Created {model._meta.object_name} pk={getattr(inst, 'pk', None)}"))
                    except Exception:
                        pass
                except Exception as exc:
                    self.stderr.write(f"Error creating curated {model._meta.object_name}: {exc}")
            else:
                self.stdout.write((f"DRYRUN curated: would create {model._meta.object_name} with {kwargs}"))

            # only create the first matching model type
            return

    # Additional per-model factories for problematic models
    def _factory__itemcatalog(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "ItemCatalog")
        except Exception:
            return
        # prefer curated Site if available; resolve the actual model behind the
        # workflow FK dynamically so this works even when 'sites' isn't declared
        site = getattr(self, "_curated_site", None)
        if site is None:
            try:
                workflow_field = model._meta.get_field("workflow")
                RelModel = workflow_field.related_model
                site = RelModel.objects.first() if RelModel else None
            except Exception:
                site = None
            if site is None and do_commit and "RelModel" in locals() and RelModel is not None:
                try:
                    candidate = RelModel(name="DevWorkflow", domain="dev.local")
                    try:
                        candidate.save()
                    except TypeError:
                        candidate.save()
                    site = candidate
                except Exception:
                    site = self._create_minimal_instance(RelModel)

        unique_suffix = uuid.uuid4().hex[:6]
        # Truncate manufacturer and size values so they fit typical DB
        # column constraints (several fields are varchar(20)).
        raw_mfg = f"ItemCatalog_mfg_{index}_{unique_suffix}"
        mfg = raw_mfg[:20]
        raw_size = f"DEV-SIZE-{index}-{unique_suffix}"
        size_val = raw_size[:30]
        defaults = {
            "size": size_val,
            "item_type": "BEV",
            "product_substrate": 70,
            "product_board": 100,
            "active": True,
        }
        # Ensure workflow is present in defaults. Note: ItemCatalog.workflow is
        # NOT NULL in the model and must be provided when creating instances.
        if site is not None:
            defaults["workflow"] = site
        else:
            # If we couldn't resolve a Site and we're committing, try to create
            # a minimal Site to satisfy foreign key constraints.
            if do_commit and apps.is_installed("sites"):
                try:
                    Site = apps.get_model("sites", "Site")
                    # Instantiate and save directly to avoid the manager.create()
                    # path passing unexpected kwargs which can fail.
                    candidate = Site(domain="dev.local", name="DevWorkflow")
                    try:
                        candidate.save()
                    except TypeError:
                        candidate.save()
                    site = candidate
                    defaults["workflow"] = site
                except Exception:
                    # Leave defaults without workflow and allow get_or_create to
                    # raise a clear IntegrityError if the workflow is missing.
                    pass
        try:
            if do_commit:
                try:
                    inst, created = model.objects.get_or_create(mfg_name=mfg, defaults=defaults)
                    if created:
                        try:
                            msg = f"Created ItemCatalog {mfg} pk={getattr(inst, 'pk', None)}"
                            self.stdout.write(msg)
                        except Exception:
                            pass
                except Exception:
                    # Fallback: attempt to instantiate and save the instance so
                    # any save-time errors surface immediately.
                    try:
                        inst = model(
                            mfg_name=mfg,
                            **{k: v for k, v in defaults.items() if v is not NOT_PROVIDED},
                        )
                        try:
                            inst.save()
                        except TypeError:
                            inst.save()
                        try:
                            msg = f"Created ItemCatalog {mfg} pk={getattr(inst, 'pk', None)}"
                            self.stdout.write(msg)
                        except Exception:
                            pass
                    except Exception as exc:
                        self.stderr.write(f"Error creating ItemCatalog (fallback): {exc}")
            else:
                try:
                    msg = f"DRYRUN curated: would get_or_create ItemCatalog mfg={mfg} defaults={defaults}"
                    self.stdout.write(msg)
                except Exception:
                    pass
        except Exception as exc:
            self.stderr.write(f"Error creating ItemCatalog: {exc}")

    def _factory__itemspec(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "ItemSpec")
        except Exception:
            return
        ItemCatalog = apps.get_model("workflow", "ItemCatalog")
        PrintLocation = apps.get_model("workflow", "PrintLocation")

        # choose or create a printlocation
        pl = None
        try:
            pl = PrintLocation.objects.first() or self._create_minimal_instance(PrintLocation)
        except Exception:
            pl = None

        # Ensure a workflow-related instance exists for ItemSpec and
        # ItemCatalog size creation steps.
        site = getattr(self, "_curated_site", None)
        if site is None:
            try:
                workflow_field = ItemCatalog._meta.get_field("workflow")
                RelModel = workflow_field.related_model
                site = RelModel.objects.first() if RelModel else None
            except Exception:
                site = None
            if site is None and do_commit and "RelModel" in locals() and RelModel is not None:
                try:
                    candidate = RelModel(name="DevWorkflow", domain="dev.local")
                    try:
                        candidate.save()
                    except TypeError:
                        candidate.save()
                    site = candidate
                except Exception:
                    site = self._create_minimal_instance(RelModel)

        unique_suffix = uuid.uuid4().hex[:6]
        # attempt to create or reuse an ItemCatalog (used as size FK)
        size_obj = None
        try:
            if site is None:
                raise Exception("no Site available for ItemCatalog creation")
            mfg = f"ItemCatalog_mfg_{index}_{unique_suffix}"
            defaults = {
                "size": f"DEV-SIZE-{index}-{unique_suffix}",
                "item_type": "BEV",
                "product_substrate": 70,
                "product_board": 100,
                "workflow": site,
                "active": True,
            }
            size_obj, _ = ItemCatalog.objects.get_or_create(mfg_name=mfg, defaults=defaults)
        except Exception:
            size_obj = ItemCatalog.objects.first() or self._create_minimal_instance(ItemCatalog)

        # Avoid creating duplicate ItemSpec for the same
        # size+printlocation by using get_or_create
        defaults = {
            "stepping_notes": f"ItemSpec_{index}_stepping_notes",
            "active": False,
            "horizontal": Decimal("10.0") * (index + 1),
            "vertical": Decimal("2.5") * (index + 1),
            "case_pack": 12 + index,
            "min_case": 6,
        }

        try:
            if do_commit:
                try:
                    inst, created = model.objects.get_or_create(size=size_obj, printlocation=pl, defaults=defaults)
                    if created:
                        try:
                            msg = (
                                "Created ItemSpec for size="
                                f"{self._repr_safe(size_obj)} "
                                f"pl={self._repr_safe(pl)} "
                                f"pk={getattr(inst, 'pk', None)}"
                            )
                            self.stdout.write(msg)
                        except Exception:
                            pass
                except Exception:
                    inst = model(
                        size=size_obj,
                        printlocation=pl,
                        **{k: v for k, v in defaults.items() if v is not NOT_PROVIDED},
                    )
                    try:
                        inst.save()
                    except TypeError:
                        inst.save()
                    self.stdout.write(f"Created ItemSpec (fallback) pk={getattr(inst, 'pk', None)}")
            else:
                try:
                    msg = (
                        "DRYRUN curated: would get_or_create ItemSpec size="
                        f"{self._repr_safe(size_obj)} "
                        f"printlocation={self._repr_safe(pl)} "
                        f"defaults={defaults}"
                    )
                    self.stdout.write(msg)
                except Exception:
                    pass
        except Exception as exc:
            self.stderr.write(f"Error creating ItemSpec: {exc}")

    def _factory__stepspec(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "StepSpec")
        except Exception:
            return
        ItemSpec = apps.get_model("workflow", "ItemSpec")
        # To satisfy UNIQUE(itemspec, special_mfg) create or choose a
        # distinct itemspec per step
        try:
            unique_suffix = uuid.uuid4().hex[:6]
            # create a minimal ItemSpec specifically for this StepSpec using
            # get_or_create patterns
            ItemCatalog = apps.get_model("workflow", "ItemCatalog")
            PrintLocation = apps.get_model("workflow", "PrintLocation")
            pl = PrintLocation.objects.first() or self._create_minimal_instance(PrintLocation)
            # prefer cached curated site
            site = getattr(self, "_curated_site", None)
            if site is None and apps.is_installed("sites"):
                Site = apps.get_model("sites", "Site")
                site = Site.objects.first() or self._create_minimal_instance(Site)
            if site is None:
                raise Exception("no Site available for ItemCatalog creation")

            mfg = f"ItemCatalog_step_mfg_{index}_{unique_suffix}"
            cat_defaults = {
                "size": f"DEV-SIZE-step-{index}-{unique_suffix}",
                "item_type": "BEV",
                "product_substrate": 70,
                "product_board": 100,
                "workflow": site,
                "active": True,
            }
            try:
                size = ItemCatalog.objects.get_or_create(mfg_name=mfg, defaults=cat_defaults)[0]
            except Exception:
                size = ItemCatalog(
                    mfg_name=mfg,
                    **{k: v for k, v in cat_defaults.items() if v is not NOT_PROVIDED},
                )
                try:
                    size.save()
                except TypeError:
                    size.save()

            itemspec_defaults = {
                "stepping_notes": f"Step_itemspec_{index}_{unique_suffix}",
                "active": True,
                "horizontal": Decimal("10.0"),
                "vertical": Decimal("2.0"),
                "case_pack": 12,
                "min_case": 6,
            }
            try:
                itemspec = ItemSpec.objects.get_or_create(size=size, printlocation=pl, defaults=itemspec_defaults)[0]
            except Exception:
                itemspec = ItemSpec(
                    size=size,
                    printlocation=pl,
                    **{k: v for k, v in itemspec_defaults.items() if v is not NOT_PROVIDED},
                )
                try:
                    itemspec.save()
                except TypeError:
                    itemspec.save()
        except Exception:
            itemspec = ItemSpec.objects.first() or self._create_minimal_instance(ItemSpec)

        special_mfg_model = apps.get_model("workflow", "SpecialMfgConfiguration")
        special = special_mfg_model.objects.first() or self._create_minimal_instance(special_mfg_model)
        # avoid duplicate (itemspec, special_mfg)
        if model.objects.filter(itemspec=itemspec, special_mfg=special).exists():
            if not do_commit:
                try:
                    msg = (
                        "DRYRUN curated: skip StepSpec (exists) itemspec="
                        f"{self._repr_safe(itemspec)} "
                        f"special={self._repr_safe(special)}"
                    )
                    self.stdout.write(msg)
                except Exception:
                    pass
            return
        kwargs = {
            "itemspec": itemspec,
            "special_mfg": special,
            "eng_num": f"StepSpec_{index}_eng_num",
            "num_colors": 4 + index,
            "status": "active",
            "template_horizontal": Decimal("50.0"),
            "template_vertical": Decimal("25.0"),
            "print_repeat": Decimal("20.0"),
            "num_blanks": 2,
            "active": True,
        }
        try:
            if do_commit:
                inst, created = model.objects.get_or_create(itemspec=itemspec, special_mfg=special, defaults=kwargs)
                if created:
                    try:
                        msg = f"Created StepSpec for itemspec={self._repr_safe(itemspec)} special={self._repr_safe(special)}"
                        self.stdout.write(msg)
                    except Exception:
                        pass
            else:
                try:
                    msg = (
                        "DRYRUN curated: would get_or_create StepSpec itemspec="
                        f"{self._repr_safe(itemspec)} "
                        f"special={self._repr_safe(special)} "
                        f"defaults={kwargs}"
                    )
                    self.stdout.write(msg)
                except Exception:
                    pass
        except Exception as exc:
            self.stderr.write(f"Error creating StepSpec: {exc}")

    def _factory__tifftopdf(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "TiffToPDF")
        except Exception:
            return
        item_model = apps.get_model("workflow", "Item") if apps.is_installed("workflow") else None
        item = None
        try:
            if item_model:
                item = item_model.objects.first() or self._create_minimal_instance(item_model)
        except Exception:
            item = None

        if item is None:
            # item is required by this model; skip to avoid NOT NULL constraint failures
            if do_commit:
                self.stderr.write(("Skipping TiffToPDF creation: no Item available to assign (would violate NOT NULL)"))
            else:
                self.stdout.write("DRYRUN curated: would skip TiffToPDF (no item available)")
            return
        # ensure item is persisted
        try:
            if getattr(item, "pk", None) is None:
                # Try to persist the instance; if it fails, fall back to obtaining
                # a minimal persisted Item to satisfy relations.
                try:
                    item.save()
                except Exception:
                    try:
                        item = self._create_minimal_instance(item_model)
                    except Exception:
                        item = None
                    if not item or getattr(item, "pk", None) is None:
                        if do_commit:
                            self.stderr.write(("Skipping TiffToPDF creation: Item could not be persisted"))
                        else:
                            self.stdout.write(("DRYRUN curated: would skip TiffToPDF (item could not be persisted)"))
                        return
        except Exception:
            pass

        kwargs = {
            "date_processed": timezone.now() - datetime.timedelta(days=index),
            "item": item,
        }
        if do_commit:
            try:
                # TEMP DIAGNOSTIC: show item identity and pk before creating queue row
                try:
                    msg = "[DIAG][TiffToPDF] item=" + repr(item) + " pk=" + str(getattr(item, "pk", None))
                    self.stderr.write(msg)
                except Exception:
                    self.stderr.write("[DIAG][TiffToPDF] item repr failed")

                inst = model(**kwargs)
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating TiffToPDF: {exc}")
        else:
            self.stdout.write(f"DRYRUN curated: would create TiffToPDF with {kwargs}")

    def _factory__colorkeyqueue(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "ColorKeyQueue")
        except Exception:
            return
        item_model = apps.get_model("workflow", "Item") if apps.is_installed("workflow") else None
        item = None
        try:
            if item_model:
                item = item_model.objects.first() or self._create_minimal_instance(item_model)
        except Exception:
            item = None

        if item is None:
            if do_commit:
                self.stderr.write(("Skipping ColorKeyQueue creation: no Item available to assign (would violate NOT NULL)"))
            else:
                self.stdout.write("DRYRUN curated: would skip ColorKeyQueue (no Item available)")
            return

        # ensure item is persisted
        try:
            if getattr(item, "pk", None) is None:
                try:
                    item.save()
                except Exception:
                    try:
                        item = self._create_minimal_instance(item_model)
                    except Exception:
                        item = None
                    if not item or getattr(item, "pk", None) is None:
                        if do_commit:
                            self.stderr.write(("Skipping ColorKeyQueue creation: Item could not be persisted"))
                        else:
                            self.stdout.write(("DRYRUN curated: would skip ColorKeyQueue (item could not be persisted)"))
                        return
        except Exception:
            pass

        kwargs = {
            "queued_at": timezone.now() - datetime.timedelta(days=index),
            "item": item,
            "priority": random.randint(1, 100),
        }
        if do_commit:
            try:
                # TEMP DIAGNOSTIC: show item identity and pk before creating queue row
                try:
                    try:
                        msg = "[DIAG][ColorKeyQueue] item=" + repr(item) + " pk=" + str(getattr(item, "pk", None))
                        self.stderr.write(msg)
                    except Exception:
                        self.stderr.write("[DIAG][ColorKeyQueue] item repr failed")
                except Exception:
                    self.stderr.write("[DIAG][ColorKeyQueue] item repr failed")
                inst = model(**{k: v for k, v in kwargs.items() if v is not None})
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating ColorKeyQueue: {exc}")
            else:
                try:
                    msg = f"DRYRUN curated: would create ColorKeyQueue with {self._safe_kwargs(kwargs)}"
                    self.stdout.write(msg)
                except Exception:
                    pass

    def _factory__qcresponse(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "QCResponse")
        except Exception:
            return
        QCCat = apps.get_model("workflow", "QCCategory")
        qccat = QCCat.objects.first() or self._create_minimal_instance(QCCat)
        QCDoc = apps.get_model("workflow", "QCResponseDoc")
        qcdoc = QCDoc.objects.first() or self._create_minimal_instance(QCDoc)
        kwargs = {
            "category": qccat,
            "qcdoc": qcdoc,
            "response": random.randint(1, 100),
            "comments": f"QCResponse_{index}_comments",
        }
        if do_commit:
            try:
                inst = model(**kwargs)
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating QCResponse: {exc}")
        else:
            try:
                msg = f"DRYRUN curated: would create QCResponse with {self._safe_kwargs(kwargs)}"
                self.stdout.write(msg)
            except Exception:
                pass

    def _factory__qcwhoops(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "QCWhoops")
        except Exception:
            return
        QCResp = apps.get_model("workflow", "QCResponse")
        qcr = QCResp.objects.first() or self._create_minimal_instance(QCResp)
        kwargs = {
            "qc_response": qcr,
            "details": f"QCWhoops_{index}_details",
            "is_valid": random.choice((True, False)),
            "artist_comments": None,
        }
        if do_commit:
            try:
                inst = model(**{k: v for k, v in kwargs.items() if v is not None})
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating QCWhoops: {exc}")
        else:
            try:
                msg = f"DRYRUN curated: would create QCWhoops with {self._safe_kwargs(kwargs)}"
                self.stdout.write(msg)
            except Exception:
                pass

    def _factory__plateorder(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "PlateOrder")
        except Exception:
            return
        User = apps.get_model("auth", "User")
        user = User.objects.first() or (users[0] if users else None)
        item_model = apps.get_model("workflow", "Item")
        item = None
        try:
            item = item_model.objects.first()
        except Exception:
            item = None

        if item is None:
            if do_commit:
                self.stderr.write(("Skipping PlateOrder creation: no Item available to assign (would violate NOT NULL)"))
            else:
                self.stdout.write("DRYRUN curated: would skip PlateOrder (no item available)")
            return

        kwargs = {
            "item": item,
            "requested_by": user,
            "date_needed": timezone.now().date(),
        }
        if do_commit:
            try:
                inst = model(**{k: v for k, v in kwargs.items() if v is not None})
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating PlateOrder: {exc}")
        else:
            self.stdout.write(f"DRYRUN curated: would create PlateOrder with {self._safe_kwargs(kwargs)}")

    def _factory__plateorderitem(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("workflow", "PlateOrderItem")
        except Exception:
            return
        PlateOrder = apps.get_model("workflow", "PlateOrder")
        order = PlateOrder.objects.first() if PlateOrder else None
        if order is None:
            if do_commit:
                self.stderr.write("Skipping PlateOrderItem creation: no PlateOrder available (would violate NOT NULL)")
            else:
                self.stdout.write("DRYRUN curated: would skip PlateOrderItem (no PlateOrder available)")
            return

        item_color_model = apps.get_model("workflow", "ItemColor")
        # use the model retrieved via apps.get_model to avoid top-level imports
        color = item_color_model.objects.first() or self._create_minimal_instance(item_color_model)
        kwargs = {"order": order, "color": color, "quantity_needed": 6 + index}
        if do_commit:
            try:
                inst = model(**kwargs)
                inst.save()
            except Exception as exc:
                self.stderr.write(f"Error creating PlateOrderItem: {exc}")
        else:
            self.stdout.write(f"DRYRUN curated: would create PlateOrderItem with {self._safe_kwargs(kwargs)}")

    def _factory__colordefinition(self, index: int, do_commit: bool, users: list):
        try:
            model = apps.get_model("color_mgt", "ColorDefinition")
        except Exception:
            return
        unique_suffix = uuid.uuid4().hex[:4]
        name = f"ColorDef_{index}_{unique_suffix}"
        coating = f"Coat_{index % 3}"
        defaults = {"description": f"Auto-generated {name}", "coating": coating}
        try:
            if do_commit:
                inst, created = model.objects.get_or_create(name=name, coating=coating, defaults=defaults)
                if created:
                    self.stdout.write(f"Created ColorDefinition {name} coating={coating}")
            else:
                self.stdout.write(f"DRYRUN curated: would get_or_create ColorDefinition name={name} coating={coating}")
        except Exception as exc:
            self.stderr.write(f"Error creating ColorDefinition: {exc}")

    def _factory__adminlog(self, index: int, do_commit: bool, users: list):
        """
        Create a safe AdminLog entry using the AdminLog.create helper.
        Prefer to attach an origin (Job then Item) if a persisted instance exists.
        """
        try:
            model = apps.get_model("admin_log", "AdminLog")
        except Exception:
            return

        origin = None
        # prefer a persisted Job as origin
        try:
            Job = apps.get_model("workflow", "Job")
            origin = Job.objects.first()
        except Exception:
            origin = None

        if origin is None:
            try:
                Item = apps.get_model("workflow", "Item")
                origin = Item.objects.first()
            except Exception:
                origin = None

        if do_commit:
            try:
                if origin and getattr(origin, "pk", None):
                    # create an error-level entry tied to the origin
                    try:
                        model.create.error(f"Auto-generated admin log {index}", origin=origin)
                    except Exception:
                        # fallback to generic info entry if error creation fails
                        model.create.info(f"Auto-generated admin log {index}")
                else:
                    # no origin available; create an info entry without origin
                    model.create.info(f"Auto-generated admin log {index}")
            except Exception as exc:
                self.stderr.write(f"Error creating AdminLog: {exc}")
        else:
            if origin and getattr(origin, "pk", None):
                self.stdout.write(f"DRYRUN curated: would create AdminLog with origin={self._repr_safe(origin)}")
            else:
                self.stdout.write("DRYRUN curated: would create AdminLog without origin")

    # Helper generators for plausible data
    def _make_string_for_field(self, model_name: str, field_name: str, index: int, field) -> str:
        """Return a plausible string value for a field based on its name."""
        name_l = field_name.lower()
        if "email" in name_l:
            return f"user{index}@example.com"
        if name_l in ("first_name", "firstname", "given_name"):
            return random.choice(("Alice", "Bob", "Charlie", "Dana", "Eve"))
        if name_l in ("last_name", "lastname", "surname"):
            return random.choice(("Smith", "Johnson", "Brown", "Williams", "Jones"))
        if "phone" in name_l or "tel" in name_l:
            return f"+1-555-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
        if "name" in name_l or "title" in name_l:
            return f"{model_name}_{field_name}_{index}"
        if "code" in name_l or "sku" in name_l or "mfg" in name_l:
            return f"{field_name.upper()}_{random.randint(1000, 9999)}"
        # default fallback
        return f"{model_name}_{index}_{field_name}"

    def _make_int_for_field(self, field_name: str) -> int:
        lname = field_name.lower()
        if "count" in lname or "qty" in lname or "quantity" in lname:
            return random.randint(1, 50)
        if "price" in lname or "amt" in lname or "amount" in lname:
            return random.randint(1, 500)
        return random.randint(1, 100)

    def _repr_safe(self, obj):
        """
        Return a safe, non-evaluating representation for common objects
        (models, lists, dicts).
        """
        try:
            # avoid importing Model at module top-level to keep Django import
            # semantics friendly
            from django.db.models import Model

            if isinstance(obj, Model):
                pk = getattr(obj, "pk", None)
                return f"<{obj.__class__.__name__}:{pk if pk is not None else 'unsaved'}>"
        except Exception:
            # not a model or django not loaded
            pass

        if isinstance(obj, dict):
            return {k: self._repr_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            typ = type(obj)
            return typ(self._repr_safe(v) for v in obj)
        # primitives
        return obj

    def _safe_kwargs(self, kwargs: dict) -> dict:
        return {k: self._repr_safe(v) for k, v in kwargs.items()}
