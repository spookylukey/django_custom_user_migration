from __future__ import absolute_import, unicode_literals

from django.apps import apps

from django_custom_user_migration.utils import change_foreign_keys, get_last_migration, find_related_apps
from .base import CustomUserCommand


class Command(CustomUserCommand):

    def handle_custom_user(self, from_app_label, from_model_name, to_app_label, to_model_name):
        forwards_backwards = """
def forwards(apps, schema_editor):
    change_foreign_keys(apps, schema_editor,
                        {from_app}, {from_model},
                        {to_app}, {to_model})

def backwards(apps, schema_editor):
    change_foreign_keys(apps, schema_editor,
                        {to_app}, {to_model},
                        {from_app}, {from_model})
        """.format(
            from_app=repr(from_app_label),
            from_model=repr(from_model_name),
            to_app=repr(to_app_label),
            to_model=repr(to_model_name),
        )

        FromModel = apps.get_model(from_app_label, from_model_name)

        # Need to ensure we depend on all related apps, otherwise the migration
        # code which find related tables won't find them all.
        extra_dependencies = [(app, get_last_migration(app)) for app in find_related_apps(FromModel)]
        self.create_runpython_migration(to_app_label, forwards_backwards,
                                        [change_foreign_keys],
                                        extra_dependencies=extra_dependencies)
