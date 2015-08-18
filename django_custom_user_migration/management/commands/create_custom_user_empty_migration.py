from .base import CustomUserPopulateCommand


class Command(CustomUserPopulateCommand):

    def handle_custom_user(self, app_label, model_name):
        self.create_populate_migration(app_label, model_name, reverse=True)
