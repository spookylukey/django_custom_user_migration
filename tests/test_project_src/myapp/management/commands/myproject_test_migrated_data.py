from __future__ import absolute_import, unicode_literals

from django.db import connection
from django.db import models
from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model

from accounts.models import MyUser as NewUser
from myapp.models import MyModel, OtherModel

# We test against CurrentUser, so that these tests
# will work whether user model is accounts.User (at end of forwards migrations)
# or auth.User (after doing forwards migrations and then backwards)
CurrentUser = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        users = CurrentUser.objects.all()
        if not len(users) > 0:
            raise AssertionError("No users created")

        user1 = CurrentUser.objects.get(username="testuser")
        user2 = CurrentUser.objects.get(username="otheruser")
        if user1.email != "test@user.com":
            raise AssertionError("user testuser doesn't have expected email address")

        if "Test Group" not in [g.name for g in user1.groups.all()]:
            raise AssertionError("user testuser doesn't have expected 'Test Group' in groups")

        mymodel = MyModel.objects.get(name="My model")
        if mymodel.owner != user1:
            raise AssertionError("MyModel.owner not pointing to right object")

        log_entries = user1.logentry_set.all()
        if len(log_entries) != 1:
            raise AssertionError("LogEntries not created for testuser")

        lg = log_entries[0]
        if lg.get_edited_object() != user2:
            raise AssertionError("LogEntry contents not migrated properly")

        other = OtherModel.objects.get(name="Some thing")
        other_owners = other.owners.all()
        if len(other_owners) != 2:
            raise AssertionError("OtherModel.owners not populated")

        if CurrentUser is NewUser:
            # end of migration - tables for auth.User will still exist, but should be empty.
            for table in ["auth_user", "auth_user_groups", "auth_user_user_permissions"]:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM {0};".format(table))
                old_rows = cursor.fetchall()
                if len(old_rows) > 0:
                    raise AssertionError("{0} table not emptied".format(table))

        if CurrentUser is NewUser:
            # end of migration
            max_user_id = max_id(CurrentUser)
            # Next line will probably raisedjango.db.utils.IntegrityError if
            # postgres auto increment ID has not been set properly.
            new_user = CurrentUser.objects.create(username='newuser1')

            # Double check
            if new_user.id != max_user_id + 1:
                raise ValueError("New user newuser1 didn't have expected id {0}".format(max_user_id + 1))

            # Should be able to do inserts on M2M tables too:
            new_user.groups.add(user1.groups.all()[0])

        if CurrentUser is not NewUser:
            # end of reverse migration
            # The newuser1 should also be present
            if not CurrentUser.objects.filter(username='newuser1').exists():
                raise ValueError("Reverse migration didn't create everything")

            max_user_id = max_id(CurrentUser)
            new_user_2 = CurrentUser.objects.create(username='newuser2')
            if new_user_2.id != max_user_id + 1:
                raise ValueError("New user newuser2 didn't have expected id {0}".format(max_user_id + 1))


def max_id(model):
    return model.objects.all().aggregate(models.Max('id'))['id__max']
