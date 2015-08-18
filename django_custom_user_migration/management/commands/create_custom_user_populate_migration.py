from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.db import models

from .base import CustomUserPopulateCommand


class Command(CustomUserPopulateCommand):

    def handle_custom_user(self, app_label, model_name):
        self.create_populate_migration(app_label, model_name, reverse=False)
