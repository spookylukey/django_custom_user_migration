from __future__ import absolute_import, unicode_literals

from django_custom_user_migration.utils import fix_contenttype
from .base import CustomUserCommand


class Command(CustomUserCommand):

    def handle_custom_user(self, from_app_label, from_model_name, to_app_label, to_model_name):
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
            from_app=repr(from_app_label),
            from_model=repr(from_model_name),
            to_app=repr(to_app_label),
            to_model=repr(to_model_name),
        )
        self.create_runpython_migration(to_app_label, forwards_backwards,
                                        [fix_contenttype])
