===============================
django_custom_user_migration
===============================

.. image:: https://img.shields.io/pypi/v/django_custom_user_migration.svg
        :target: https://pypi.python.org/pypi/django_custom_user_migration


django_custom_user_migration creates migrations for you to move an existing
Django project that uses ``django.contrib.auth.models.User`` to using a custom user
model.

Free software: BSD license

Use case
--------

You are currently using Django's ``django.contrib.auth.models.User`` model in a
deployed project, but want to migrate to a model that is under your own control, or
provided by a 3rd party.

Other solutions
---------------

See https://code.djangoproject.com/ticket/25313 which probably works better at this point in time,
or https://www.caktusgroup.com/blog/2019/04/26/how-switch-custom-django-user-model-mid-project/ .

Prerequisites
-------------

* Django 1.8 or later.

  Django 1.10 and later currently do not work - see `issue 5 <https://bitbucket.org/spookylukey/django_custom_user_migration/issues/5/inconsistentmigrationhistory-when>`_.

* Python 2.7 or Python 3.3+

You must have ensured that everywhere in your project (including 3rd party
libraries) you are using ``AUTH_USER_MODEL`` and
``django.contrib.auth.get_user_model()`` rather than ``"auth.User"`` and
``django.contrib.auth.models.User``.


Usage
-----

There are a lot of steps below, but it is almost all copy/paste, and with no
complications you could be done in 5 minutes. It assumed you will perform all
these steps apart from the last in your development environment.

1. Install ``django_custom_user_migration`` to your project::

     pip install django_custom_user_migration

2. Add ``"django_custom_user_migration"`` to your ``INSTALLED_APPS``.

   You now have some management commands for creating migrations that we
   will use later.

3. Create a custom user model which is identical to Django's ``auth.User``, but
   in an app in your own project. For this process to work correctly, you will
   need to create a new app for this model - we'll call it ``accounts`` from now
   on::

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

   This migration must be ``0001_initial`` or you will have problems later on,
   as mentioned in the docs for `AUTH_USER_MODEL
   <https://docs.djangoproject.com/en/1.8/ref/settings/#auth-user-model>`_.

   The migration will also create M2M tables for the M2M fields specified
   on ``AbstractUser`` itself.

5. Create a data migration that will populate these tables from ``auth.User``::

     ./manage.py create_custom_user_populate_migration auth.User accounts.User

   All the commands to create migrations take arguments <from_model> <to_model> like this.

6. Create a schema migration that will alter every FK that points at ``auth.User``
   to point at your model instead::

     ./manage.py create_custom_user_schema_migration auth.User accounts.User

7. Create a data migration that will fix up the contenttypes tables::

     ./manage.py create_custom_user_contenttypes_migration auth.User accounts.User

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

      ./manage.py create_custom_user_empty_migration auth.User accounts.User

13. Run all the migrations::

      ./manage.py migrate

14. Test everything!

    Note that all migrations generated are reversible, but before running them
    in reverse you should set AUTH_USER_MODEL back to ``"auth.User"``, and you
    will also therefore need to use the
    ``django_custom_user_migration.models.AbstractModel`` as a base class or you
    will get validation errors that prevent migrations from running.

    When running Django unit tests, you may have problems when Django attempts
    to run your migrations in a test database. Since your AUTH_USER_MODEL no
    longer points to ``auth.User``, that table won't be created and the
    migrations which expect it to exist will fail.

    In the short term, this can be fixed as per this advice:
    http://stackoverflow.com/a/28560805/182604

    Long term, this can be fixed by squashing the ``accounts`` migrations up to
    step 12 into a single migration. Use the ``squashmigrations`` command to do
    this, then manually edit it to remove all but the initial ``CreateModel``
    operation. So the migration created should be the same as accounts
    ``0001_initial``, but it will have a ``replaces`` attribute that marks it as
    squashing the others. You may also need to adjust (remove) some of its
    dependencies.

15. Uninstall ``django_custom_user_migration``, and remove it from your
    ``INSTALLED_APPS``, you don't need it any more. The migrations generated
    run without it being installed.

16. You can now deploy these migrations to your production environment and run
    them in the normal way using ``./manage.py migrate``.

You can now customise your ``User`` model as required in the normal way, using
migrations etc. You could even make it inherit from ``AbstractBaseUser`` or some
other model instead of ``AbstractUser``, provided that you write/generate the
necessary data migrations to cope with missing fields, and update your admin and
application accordingly.


Other notes
-----------

* Use at own risk, make sure you back up your data first, etc. etc.

* Tested on sqlite and postgres

* If you have other tables with FKs to ``auth.User`` that Django doesn't know
  about, you will have to deal with those manually with a custom migration. (In
  really old Django projects, you might have old tables like 'auth_message'
  kicking around which you'll need to delete).

* Almost everything included in this library is generic regarding the models
  involved, and uses introspection rather than hard-coding things about
  ``auth.User``. The main exception is
  ``django_custom_user_migration.models.AbstractUser``, which is a copy-paste
  job from Django sources.

  This means that you may be able to use the code here to migrate other
  swappable models. This has not been tested however.
