#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os.path
import shutil
import subprocess
import unittest


class TestProcessBase(object):

    def setUp(self):
        self.copy_test_project()
        self.set_db()

    def tearDown(self):
        self.delete_test_project()

    def test_process(self):
        # Testing migrations etc. is really hard in Django.
        # Instead of that, we test the entire process,
        # using commandline, and starting with a project
        # that doesn't use a custom User model.

        # Create initial database
        self.shell("./manage.py migrate")

        # Custom management command to create initial data
        self.shell("./manage.py myproject_create_test_data")

        # These steps follow README.rst closely

        # Step 1 - not needed
        # Step 2:
        self.add_to_installed_apps("django_custom_user_migration")
        # Step 3:
        self.create_custom_user_model()
        self.add_to_installed_apps("accounts")
        # Step 4:
        self.shell("./manage.py makemigrations accounts")
        # Step 5:
        self.shell("./manage.py create_custom_user_populate_migration auth.User accounts.MyUser")
        # Step 6:
        self.shell("./manage.py create_custom_user_schema_migration auth.User accounts.MyUser")
        # Step 7:
        self.shell("./manage.py create_custom_user_contenttypes_migration auth.User accounts.MyUser")
        # Step 8:
        self.replace_user_import("from django_custom_user_migration.models import AbstractUser",
                                 "from django.contrib.auth.models import AbstractUser")
        # Step 9:
        self.set_auth_user_model("accounts.MyUser")
        # Step 10:
        self.shell("./manage.py makemigrations accounts")
        # Step 11 - skip
        # Step 12:
        self.shell("./manage.py create_custom_user_empty_migration auth.User accounts.MyUser")
        # Step 13:
        self.shell("./manage.py migrate --noinput")
        # Step 14:
        # Custom management command to test migrated data
        self.shell("./manage.py myproject_test_migrated_data")

        # Test reverse migrations
        self.set_auth_user_model("auth.User")
        self.replace_user_import("from django.contrib.auth.models import AbstractUser",
                                 "from django_custom_user_migration.models import AbstractUser")
        self.shell("./manage.py migrate accounts zero")
        self.shell("./manage.py myproject_test_migrated_data")

    def copy_test_project(self):
        self.delete_test_project()
        shutil.copytree("tests/test_project_src",
                        "test_project")

    def delete_test_project(self):
        shutil.rmtree("test_project", ignore_errors=True)

    def shell(self, command):
        """Run a shell command, from inside test_project dir"""
        subprocess.check_call("cd test_project; " + command, shell=True)

    def add_to_installed_apps(self, item):
        self.change_file_chunk("test_project/myapp/settings.py",
                               "    # INSTALLED_APPS_start",
                               "    # INSTALLED_APPS_end",
                               lambda chunk: chunk + repr(item) + ",\n")

    def set_databases_setting(self, text):
        self.change_file_chunk("test_project/myapp/settings.py",
                               "# DATABASES_start",
                               "# DATABASES_end",
                               lambda chunk: text)

    def change_file_chunk(self, filename, start_marker, end_marker, replace_func):
        with change_file(filename) as f:
            before, after = f.contents.split(start_marker)
            middle, after = after.split(end_marker)
            middle = replace_func(middle)
            settings_file = before + start_marker + middle + end_marker + after
            f.write(settings_file)

    def create_custom_user_model(self):
        self.shell("mkdir accounts")
        self.shell("touch accounts/__init__.py")
        with open("test_project/accounts/models.py", "wb") as f:
            f.write("""
from django_custom_user_migration.models import AbstractUser

class MyUser(AbstractUser):
    pass
            """.encode('utf-8'))

    def replace_user_import(self, from_import, to_import):
        with change_file("test_project/accounts/models.py") as f:
            f.write(f.contents.replace(from_import, to_import))

    def set_auth_user_model(self, model_path):
        with change_file("test_project/myapp/settings.py") as f:
            f.write(f.contents + "\nAUTH_USER_MODEL = {0}\n".format(repr(model_path)))


class TestProcessSqlite(TestProcessBase, unittest.TestCase):

    def set_db(self):
        self.set_databases_setting("""
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tests.db"
    }
}
""")


class TestProcessPostgres(TestProcessBase, unittest.TestCase):

    def setUp(self):
        super(TestProcessPostgres, self).setUp()
        self.clear_db()

    def tearDown(self):
        self.clear_db()
        super(TestProcessPostgres, self).tearDown()

    def clear_db(self):
        import psycopg2
        with psycopg2.connect(database="django_custom_user_migration_tests",
                              user="django_custom_user_migration_tests",
                              password="test") as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [r[0] for r in cursor.fetchall()]
            for t in tables:
                cursor.execute("DROP TABLE IF EXISTS {0} CASCADE;".format(t))

    def set_db(self):
        self.set_databases_setting("""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_custom_user_migration_tests',
        'USER': 'django_custom_user_migration_tests',
        'PASSWORD': 'test',
        'HOST': 'localhost',
        'PORT': 5432,
        'CONN_MAX_AGE': 30,
    }
}
""")


class change_file(object):
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        with open(self.filename) as f:
            self.contents = f.read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.filename, "wb") as f:
            f.write(self.contents.encode('utf-8'))
        if self.filename.endswith(".py"):
            pyc = self.filename.replace(".py", ".pyc")
            if os.path.exists(pyc):
                os.unlink(pyc)
        return False

    def write(self, val):
        self.contents = val
