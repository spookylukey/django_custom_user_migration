from __future__ import absolute_import, unicode_literals

from django.db.migrations.loader import MigrationLoader
from django.db import models


def find_related_apps(model):
    related_models = [rel.related_model for rel in model._meta.get_fields(include_hidden=True)
                      if hasattr(rel, 'field') and isinstance(rel.field, models.ForeignKey)]

    return list(sorted(set([m._meta.app_label for m in related_models])))


def get_last_migration(app_label):
    loader = MigrationLoader(None, ignore_no_migrations=True)
    graph = loader.graph
    leaf_nodes = graph.leaf_nodes()
    for leaf in leaf_nodes:
        if leaf[0] == app_label:
            return leaf[1]


def populate_table(apps, schema_editor, from_app, from_model, to_app, to_model):
    import math

    FromModel = apps.get_model(from_app, from_model)
    ToModel = apps.get_model(to_app, to_model)

    # FromModel.objects is not available, because it has been swapped out,
    # but we can use _default_manager

    max_id = FromModel._default_manager.order_by('-id')[0].id

    # Use batches to avoid loading entire table into memory
    BATCH_SIZE = 200

    # Careful with off-by-one errors where max_id is a multiple of BATCH_SIZE
    for batch_num in range(0, int(math.floor(max_id / BATCH_SIZE)) + 1):
        start = batch_num * BATCH_SIZE
        stop = start + BATCH_SIZE
        old_rows = list(FromModel._default_manager.order_by('id')[start:stop])

        new_rows = [ToModel(**{k: v for k, v in u.__dict__.items()
                               if not k.startswith('_')})
                    for u in old_rows]

        ToModel.objects.bulk_create(new_rows)


def empty_table(apps, schema_editor, from_app, from_model):
    ToModel = apps.get_model(from_app, from_model)
    ToModel._default_manager.all().delete()


def change_foreign_keys(apps, schema_editor, from_app, from_model_name, to_app, to_model_name):
    from django.db import models

    FromModel = apps.get_model(from_app, from_model_name)
    ToModel = apps.get_model(to_app, to_model_name)

    # We don't make assumptions about which model is being pointed to by
    # AUTH_USER_MODEL. So include fields from both FromModel and ToModel.
    # For the sake of M2M tables

    # Only one of them will actually have FK fields pointing to them.

    fields = FromModel._meta.get_fields(include_hidden=True) + ToModel._meta.get_fields(include_hidden=True)

    for rel in fields:
        if not hasattr(rel, 'field') or not isinstance(rel.field, models.ForeignKey):
            continue
        fk_field = rel.field
        f_name, f_field_name, pos_args, kw_args = fk_field.deconstruct()
        kw_args['to'] = ToModel
        new_field = fk_field.__class__(*pos_args, **kw_args)
        new_field.name = fk_field.name
        new_field.column = fk_field.column
        new_field.model = fk_field.model
        schema_editor.alter_field(fk_field.model, fk_field, new_field, strict=True)

        m = fk_field.model
        print("Fixing FK in {0}.{1}".format(m._meta.app_label, m.__name__))


def fix_contenttype(apps, schema_editor, from_app, from_model, to_app, to_model):
    from_model, to_model = from_model.lower(), to_model.lower()
    schema_editor.execute("UPDATE django_content_type SET app_label=%s, model=%s WHERE app_label=%s AND model=%s;",
                          [to_app, to_model, from_app, from_model])
