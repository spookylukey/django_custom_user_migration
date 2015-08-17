from __future__ import absolute_import, unicode_literals

import inspect

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.migrations import Migration
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.writer import MigrationWriter


FROM_APP = "auth"
FROM_MODEL = "User"


class CustomUserCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("custom_user_model")

    def handle(self, *args, **options):
        model = options['custom_user_model']
        app_label, model_name = model.split(".")
        self.handle_custom_user(app_label, model_name)

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
                migration_string = migration_string.replace("operations = [",
                                                            "operations = [\n"
                                                            "        migrations.RunPython(forwards, backwards),")
                with open(writer.path, "wb") as fh:
                    fh.write(migration_string.encode('utf-8'))
