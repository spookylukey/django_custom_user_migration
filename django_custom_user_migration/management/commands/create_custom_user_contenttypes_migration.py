from __future__ import absolute_import, unicode_literals

from django_custom_user_migration.utils import fix_contenttype
from .base import CustomUserCommand, FROM_APP, FROM_MODEL


class Command(CustomUserCommand):

    def handle_custom_user(self, app_label, model_name):
        forwards_backwards = """
def forwards(apps, schema_editor):
    fix_contenttype(apps, schema_editor,
                    {from_app}, {from_model},
                    {to_app}, {to_model})


def backwards(apps, schema_editor):
    fix_contenttype(apps, schema_editor,
                    {to_app}, {to_model},
                    {from_app}, {from_model})
        """.format(
            from_app=repr(FROM_APP),
            from_model=repr(FROM_MODEL),
            to_app=repr(app_label),
            to_model=repr(model_name),
        )
        self.create_runpython_migration(app_label, forwards_backwards,
                                        [fix_contenttype])
