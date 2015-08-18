from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.db import models

from .base import CustomUserCommand, FROM_APP, FROM_MODEL

from django_custom_user_migration.utils import populate_table, empty_table, make_table_name, fetch_with_column_names


class Command(CustomUserCommand):

    def handle_custom_user(self, app_label, model_name):
        populate_template = """
    populate_table(apps, schema_editor,
                   {from_app}, {from_model},
                   {to_app}, {to_model})
"""
        empty_template = """
    empty_table(apps, schema_editor,
                {to_app}, {to_model})
"""

        forwards_backwards = """
def forwards(apps, schema_editor):
    {populate}


def backwards(apps, schema_editor):
    {empty}
        """

        from_model = apps.get_model(FROM_APP, FROM_MODEL)
        to_model = apps.get_model(app_label, model_name)

        # We need to populate the model table, but also the automatically
        # created M2M tables from the corresponding table on the source model

        model_pairs = [(from_model, to_model)]

        for f in from_model._meta.get_fields(include_hidden=True):
            if not isinstance(f, models.ManyToManyField):
                continue
            model_pairs.append((f.rel.through, to_model._meta.get_field(f.name).rel.through))

        populate = ""
        empty = ""
        for (from_m, to_m) in model_pairs:
            populate += populate_template.format(
                from_app=repr(from_m._meta.app_label),
                from_model=repr(from_m.__name__),
                to_app=repr(to_m._meta.app_label),
                to_model=repr(to_m.__name__),
            )

        for (from_m, to_m) in reversed(model_pairs):
            empty += empty_template.format(
                from_app=repr(from_m._meta.app_label),
                from_model=repr(from_m.__name__),
                to_app=repr(to_m._meta.app_label),
                to_model=repr(to_m.__name__),
            )

        forwards_backwards = forwards_backwards.format(populate=populate,
                                                       empty=empty)

        self.create_runpython_migration(app_label, forwards_backwards,
                                        [populate_table, empty_table, make_table_name, fetch_with_column_names])
