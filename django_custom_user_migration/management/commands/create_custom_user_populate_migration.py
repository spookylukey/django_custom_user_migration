from __future__ import absolute_import, unicode_literals

from .base import CustomUserCommand, FROM_APP, FROM_MODEL

from django_custom_user_migration.utils import populate_table, empty_table


class Command(CustomUserCommand):

    def handle_custom_user(self, app_label, model_name):
        forwards_backwards = """
def forwards(apps, schema_editor):
    populate_table(apps, schema_editor,
                   {from_app}, {from_model},
                   {to_app}, {to_model})


def backwards(apps, schema_editor):
    empty_table(apps, schema_editor,
                {to_app}, {to_model})
        """.format(
            from_app=repr(FROM_APP),
            from_model=repr(FROM_MODEL),
            to_app=repr(app_label),
            to_model=repr(model_name),
        )

        self.create_runpython_migration(app_label, forwards_backwards, [populate_table, empty_table])
