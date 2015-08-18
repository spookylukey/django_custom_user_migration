#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os.path
import shutil
import subprocess
import unittest


class TestCreateCustomUserMigration(unittest.TestCase):

    def setUp(self):
        self.copy_test_project()

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
        SPLIT_START = "    # INSTALLED_APPS_start"
        SPLIT_END = "    # INSTALLED_APPS_end"
        with change_file("test_project/myapp/settings.py") as f:
            before, after = f.contents.split(SPLIT_START)
            middle, after = after.split(SPLIT_END)
            middle += "    " + repr(item) + ",\n"
            settings_file = before + SPLIT_START + middle + SPLIT_END + after
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
