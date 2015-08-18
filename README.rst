===============================
django_custom_user_migration
===============================

.. image:: https://img.shields.io/pypi/v/django_custom_user_migration.svg
        :target: https://pypi.python.org/pypi/django_custom_user_migration


django_custom_user_migration will help you create a migration to using a custom
User model with Django

* Free software: BSD license

Use case
--------

You are currently using Django's ``django.contrib.auth.models.User`` model in a
deployed project, but want to migrate to a model that is under your own control, or
provided by a 3rd party.

Prerequisites
-------------

* Django 1.7 or later
* Python 2.7 or Python 3.3+

You must have ensured that everywhere in your project (including 3rd party
libraries) you are using ``AUTH_USER_MODEL`` and
``django.contrib.auth.get_user_model()`` rather than ``"auth.User"`` and
``django.contrib.auth.models.User``.


Usage
-----

1. Install ``django_custom_user_migration`` to your project::

     pip install django_custom_user_migration

2. Add ``"django_custom_user_migration"`` to your ``INSTALLED_APPS``.

   You now have some management commands for creating migrations that we
   will use later.

3. Create a custom user model which is identical to Django's ``auth.User``, but
   in an app in your own project. For this process to work correctly, you will
   need to create a new, dedicated app just for this model - we'll call it
   ``accounts`` from now on::

     # accounts/models.py

     from django_custom_user_migration.models import AbstractUser

     class User(AbstractUser):
         pass

   The model can be called anything you want. Remember to add this app to your
   ``INSTALLED_APPS``.

   Don't add additional fields at this point, and don't change
   ``AUTH_USER_MODEL`` yet.

   We avoid using ``django.contrib.auth.models.AbstractUser`` at this point, or
   a user model from some 3rd party library, because we get problems with
   ``related_name`` clashes that we can't work around. Later on, we'll change to
   inheriting from ``django.contrib.auth.AbstractUser``, and then to another model
   if necessary.

4. Create a normal migration to create the table for this::

     ./manage.py makemigrations accounts

   This migration must be ``0001_initial`` or you will have problems later on.

5. Create a data migration that will populate this table from ``auth.User``::

     ./manage.py create_custom_user_populate_migration accounts.User

6. Create a schema migration that will alter every FK that points at ``auth.User``
   to point at your model instead::

     ./manage.py create_custom_user_schema_migration accounts.User

7. Create a data migration that will fix up the contenttypes tables::

     ./manage.py create_custom_user_contenttypes_migration accounts.User

8. Change the ``AbstractUser`` import in your models.py to::

      from django.contrib.auth.models import AbstractUser

9. Change ``AUTH_USER_MODEL`` to ``"accounts.User"`` in your settings.

10. Run ``makemigrations`` again::

      ./manage.py makemigrations accounts

    This creates a migration that doesn't actually change fields, but is needed
    for Django to think that everything lines up again.

11. Do related changes for admin etc. as described in Django docs:
    https://docs.djangoproject.com/en/dev/topics/auth/customizing/#extending-django-s-default-user

    Simplest version::

      # accounts/admin.py

      from django.contrib import admin
      from django.contrib.auth.admin import UserAdmin
      from . models import User

      admin.site.register(User, UserAdmin)

12. Create a migration that empties the ``auth.User`` table::

      ./manage.py create_custom_user_empty_migration accounts.User

13. Run all the migrations::

      ./manage.py migrate

    All the migrations are reversible, so you should be able to get back to
    previous states. Obviously, you would test this thoroughly before doing it
    in production.

14. Test everything!

    Note that all migrations generated are reversible, but before running them
    in reverse you should set AUTH_USER_MODEL back to `"auth.User"`, and you
    will also therefore need to use the
    ``django_custom_user_migration.models.AbstractModel`` as a base class or you
    will get validation errors that prevent migrations from running.

15. Uninstall ``django_custom_user_migration``, you don't need it any more. The
    migrations generated run without it being installed.


You can now customise your ``User`` model as required in the normal way, using
migrations etc. You could even make it inherit from ``AbstractBaseUser`` or some
other model instead of ``AbstractUser``, provided that you write/generate the
necessary data migrations to cope with missing fields, and update your admin and
application accordingly.
