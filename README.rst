===============================
django_custom_user_migration
===============================

.. image:: https://img.shields.io/pypi/v/django_custom_user_migration.svg
        :target: https://pypi.python.org/pypi/django_custom_user_migration


django_custom_user_migration will help you create a migration to using a custom User model with Django

* Free software: BSD license
* Documentation: https://django_custom_user_migration.readthedocs.org.

Use case
--------

You are currently using Django's ``django.contrib.auth.models.User`` model, but
want to migrate to a model that is under your own control (or provided by a 3rd party).


Prerequisites
-------------

* Django 1.7 or later
* Python 2.7 or Python 3.3 or later


Usage
-----

1. Install ``django_custom_user_migration`` to your project::

     pip install django_custom_user_migration

2. Add ``"django_custom_user_migration"`` to your ``INSTALLED_APPS``.


3. Create a custom user model which is identical to Django's ``auth.User``, but
   in an app in your own project (we'll call it ``myapp`` from now on)::

     # myapp/models.py

     from django.contrib.auth.models import AbstractUser

     class MyUser(AbstractUser):
         pass


   Do not changes ``AUTH_USER_MODEL`` at this point.

4. Create a normal migration to create the table for this::

     ./manage.py makemigrations myapp
