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


def make_table_name(apps, app, model):
    try:
        m = apps.get_model(app, model)
        if m._meta.db_table:
            return m._meta.db_table
    except LookupError:
        pass  # for M2M fields
    return "{0}_{1}".format(app, model).lower()


def fetch_with_column_names(schema_editor, sql, params):
    c = schema_editor.connection.cursor()
    c.execute(sql, params)
    rows = c.fetchall()
    return rows, [r[0] for r in c.description]


def populate_table(apps, schema_editor, from_app, from_model, to_app, to_model):
    # Due to swapped out models, which means that some model classes (and/or
    # their auto-created M2M tables) do not exist or don't function correctly,
    # it is better to use SELECT / INSERT than attempting to use ORM.
    import math

    from_table_name = make_table_name(apps, from_app, from_model)
    to_table_name = make_table_name(apps, to_app, to_model)

    max_id = fetch_with_column_names(schema_editor, "SELECT MAX(id) FROM {0};".format(from_table_name), [])[0][0][0]
    if max_id is None:
        max_id = 1

    # Use batches to avoid loading entire table into memory
    BATCH_SIZE = 100

    # Careful with off-by-one errors where max_id is a multiple of BATCH_SIZE
    for batch_num in range(0, int(math.floor(max_id / BATCH_SIZE)) + 1):
        start = batch_num * BATCH_SIZE
        stop = start + BATCH_SIZE
        ops = schema_editor.connection.ops
        old_rows, old_cols = fetch_with_column_names(schema_editor,
                                                     "SELECT * FROM {0} WHERE id >= %s AND id < %s;".format(
                                                         ops.quote_name(from_table_name)),
                                                     [start, stop])

        # The column names in the new table aren't necessarily the same
        # as in the old table - things like 'user_id' vs 'myuser_id'.
        # We have to map them, and this seems to be good enough for our needs:
        base_from_model = from_model.split("_")[0]
        base_to_model = to_model.split("_")[0]
        map_fk_col = lambda c: "{0}_id".format(base_to_model).lower() if c == "{0}_id".format(base_from_model).lower() else c
        new_cols = list(map(map_fk_col, old_cols))

        for row in old_rows:
            values_sql = ", ".join(["%s"] * len(new_cols))
            columns_sql = ", ".join(ops.quote_name(col_name) for col_name in new_cols)
            sql = "INSERT INTO {0} ({1}) VALUES ({2});".format(ops.quote_name(to_table_name),
                                                               columns_sql,
                                                               values_sql)

            # could collect and do 'executemany', but sqlite doesn't let us
            # execute more than one statement at once it seems.
            schema_editor.execute(sql, row)


def empty_table(apps, schema_editor, from_app, from_model):
    from_table_name = make_table_name(apps, from_app, from_model)
    ops = schema_editor.connection.ops
    schema_editor.execute("DELETE FROM {0};".format(ops.quote_name(from_table_name)))


def change_foreign_keys(apps, schema_editor, from_app, from_model_name, to_app, to_model_name):
    FromModel = apps.get_model(from_app, from_model_name)
    ToModel = apps.get_model(to_app, to_model_name)

    # We don't make assumptions about which model is being pointed to by
    # AUTH_USER_MODEL. So include fields from both FromModel and ToModel.
    # Only one of them will actually have FK fields pointing to them.

    print()
    fields = FromModel._meta.get_fields(include_hidden=True) + ToModel._meta.get_fields(include_hidden=True)

    for rel in fields:
        if not hasattr(rel, 'field') or not isinstance(rel.field, models.ForeignKey):
            continue
        fk_field = rel.field

        f_name, f_field_name, pos_args, kw_args = fk_field.deconstruct()

        # fk_field might have been the old or new one. We need to fix things up.
        old_field_kwargs = kw_args.copy()
        old_field_kwargs['to'] = FromModel
        old_field = fk_field.__class__(*pos_args, **old_field_kwargs)
        old_field.model = fk_field.model

        new_field_kwargs = kw_args.copy()
        new_field_kwargs['to'] = ToModel
        new_field = fk_field.__class__(*pos_args, **new_field_kwargs)
        new_field.model = fk_field.model

        if fk_field.model._meta.auto_created:
            # If this is a FK that is part of an M2M on the model itself,
            # we've already dealt with this, by virtue of the data migration
            # that populates the auto-created M2M field.
            if fk_field.model._meta.auto_created in [ToModel, FromModel]:
                print("Skipping {0}".format(repr(rel)))
                continue

            # In this case (FK fields that are part of an autogenerated M2M),
            # the column name in the new M2M might be different to that in the
            # old M2M. This makes things much harder, and involves duplicating
            # some Django logic.

            # Build a correct ForeignKey field, as it should
            # have been on FromModel
            old_field.name = from_model_name.lower()
            old_field.column = "{0}_id".format(old_field.name)

            # build a correct ForeignKey field, as it should
            # be on ToModel
            new_field.name = to_model_name.lower()
            new_field.column = "{0}_id".format(new_field.name)
        else:
            old_field.name = fk_field.name
            old_field.column = fk_field.column
            new_field.name = fk_field.name
            new_field.column = fk_field.column

        show = lambda m: "{0}.{1}".format(m._meta.app_label, m.__name__)
        print("Fixing FK in {0}, col {1} -> {2}, from {3} -> {4}".format(
            show(fk_field.model),
            old_field.column, new_field.column,
            show(old_field.rel.to), show(new_field.rel.to),
        ))
        schema_editor.alter_field(fk_field.model, old_field, new_field, strict=True)


def fix_contenttype(apps, schema_editor, from_app, from_model, to_app, to_model):
    from_model, to_model = from_model.lower(), to_model.lower()
    schema_editor.execute("UPDATE django_content_type SET app_label=%s, model=%s WHERE app_label=%s AND model=%s;",
                          [to_app, to_model, from_app, from_model])
