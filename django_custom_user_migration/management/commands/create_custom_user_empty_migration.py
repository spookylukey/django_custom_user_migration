from .base import CustomUserPopulateCommand


class Command(CustomUserPopulateCommand):

    def handle_custom_user(self, from_app_label, from_model_name, to_app_label, to_model_name):
        self.create_populate_migration(from_app_label, from_model_name, to_app_label, to_model_name, reverse=True)
