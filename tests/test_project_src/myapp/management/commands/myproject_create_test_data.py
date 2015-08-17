from django.contrib.admin.models import LogEntry, ContentType, ADDITION
from django.contrib.auth.models import User, Group

from django.core.management.base import BaseCommand

from myapp.models import MyModel


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        user1 = User.objects.create_user("testuser", email="test@user.com")
        user2 = User.objects.create_user("otheruser", email="other@user.com")
        group1 = Group.objects.create(name="Test Group")

        user1.groups.add(group1)

        MyModel.objects.create(name="My model", owner=user1)

        # Create a dummy log entry for a change on user2, by user1
        LogEntry.objects.log_action(
            user1.id,
            ContentType.objects.get_for_model(User).id,
            user2.id,
            repr(user2),
            ADDITION,
            change_message="testuser created otheruser",
        )
