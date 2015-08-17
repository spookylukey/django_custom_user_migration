from __future__ import absolute_import, unicode_literals

from django.db import models

from django.conf import settings


class MyModel(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
