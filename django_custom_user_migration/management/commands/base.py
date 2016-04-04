from __future__ import absolute_import, unicode_literals

import inspect

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models
from django.db.migrations import Migration
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.writer import MigrationWriter

from django_custom_user_migration.utils import (empty_table, fetch_with_column_names, get_max_id,
                                                make_table_name, populate_table, reset_sequence)


class CustomUserCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("source_model")
        parser.add_argument("destination_model")

    def handle(self, *args, **options):
        source_model = options['source_model']
        destination_model = options['destination_model']
        from_app_label, from_model_name = source_model.split(".")
        to_app_label, to_model_name = destination_model.split(".")
        self.handle_custom_user(from_app_label, from_model_name, to_app_label, to_model_name)

    def create_runpython_migration(self, app_label, forwards_backwards, extra_functions,
                                   extra_dependencies=None):

        # Copy source code, so that we can uninstall this helper app
        # and the migrations still work.
        extra_func_code = "\n\n".join(inspect.getsource(f)
                                      for f in extra_functions)

        loader = MigrationLoader(None, ignore_no_migrations=True)
        autodetector = MigrationAutodetector(
            loader.project_state(),
            ProjectState.from_apps(apps),
            None,
        )

        changes = {
            app_label: [Migration("custom", app_label)]
        }
        changes = autodetector.arrange_for_graph(
            changes=changes,
            graph=loader.graph,
        )

        for app_label, app_migrations in changes.items():
            for migration in app_migrations:
                if extra_dependencies is not None:
                    migration.dependencies.extend(extra_dependencies)
                writer = MigrationWriter(migration)

                migration_string = writer.as_string().decode('utf-8')

                # Add support functions:
                migration_string = migration_string.replace("\nclass Migration",
                                                            forwards_backwards + "\n\n" +
                                                            extra_func_code + "\n\n" +
                                                            "\nclass Migration")

                # Add operations:
                migration_string = migration_string.replace(
                    "operations = [",
                    "operations = [\n"
                    "        migrations.RunPython(forwards, backwards),")
                with open(writer.path, "wb") as fh:
                    fh.write(migration_string.encode('utf-8'))


class CustomUserPopulateCommand(CustomUserCommand):

    def create_populate_migration(self, from_app_label, from_model_name,
                                  to_app_label, to_model_name, reverse=False):
        populate_template = """
    populate_table(apps, schema_editor,
                   "{from_app}", "{from_model}",
                   "{to_app}", "{to_model}")"""
        empty_template = """
    empty_table(apps, schema_editor,
                "{to_app}", "{to_model}")"""

        forwards_backwards_template = """
def forwards(apps, schema_editor):{forwards}


def backwards(apps, schema_editor):{backwards}
"""

        from_model = apps.get_model(from_app_label, from_model_name)
        to_model = apps.get_model(to_app_label, to_model_name)
        if reverse:
            from_model, to_model = to_model, from_model

        # We need to populate the model table, but also the automatically
        # created M2M tables from the corresponding table on the source model
        model_pairs = [((from_model._meta.app_label, from_model.__name__),
                        (to_model._meta.app_label, to_model.__name__))]

        for from_f in from_model._meta.get_fields(include_hidden=True):
            if not isinstance(from_f, models.ManyToManyField):
                continue
            to_f = to_model._meta.get_field(from_f.name)

            # When auth.User has been swapped out, the f.rel.through attribute
            # becomes None. So we have to build the name manually.
            make_name = lambda f: "{0}_{1}".format(f.model.__name__, f.name)
            model_pairs.append(((from_model._meta.app_label, make_name(from_f)),
                                (to_model._meta.app_label, make_name(to_f))))

        populate = ""
        empty = ""
        for ((from_a, from_m), (to_a, to_m)) in model_pairs:
            populate += populate_template.format(
                from_app=from_a,
                from_model=from_m,
                to_app=to_a,
                to_model=to_m,
            )

        # Empty in reverse order i.e. M2M tables first
        for ((from_a, from_m), (to_a, to_m)) in reversed(model_pairs):
            empty += empty_template.format(
                from_app=from_a,
                from_model=from_m,
                to_app=to_a,
                to_model=to_m,
            )

        if not reverse:
            data = {'forwards': populate,
                    'backwards': empty,
                    }
        else:
            data = {'forwards': empty,
                    'backwards': populate,
                    }
        forwards_backwards = forwards_backwards_template.format(**data)

        self.create_runpython_migration(to_app_label, forwards_backwards,
                                        [populate_table, empty_table, make_table_name,
                                         fetch_with_column_names, get_max_id,
                                         reset_sequence])
