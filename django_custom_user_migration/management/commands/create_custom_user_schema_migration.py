from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model

from django_custom_user_migration.utils import change_foreign_keys, get_last_migration, find_related_apps
from .base import CustomUserCommand, FROM_APP, FROM_MODEL


class Command(CustomUserCommand):

    def handle_custom_user(self, app_label, model_name):
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
            from_app=repr(FROM_APP),
            from_model=repr(FROM_MODEL),
            to_app=repr(app_label),
            to_model=repr(model_name),
        )

        User = get_user_model()
        # Need to ensure we get all related apps,

        extra_dependencies = [(app, get_last_migration(app)) for app in find_related_apps(User) + ["auth"]]
        self.create_runpython_migration(app_label, forwards_backwards,
                                        [change_foreign_keys],
                                        extra_dependencies=extra_dependencies)
