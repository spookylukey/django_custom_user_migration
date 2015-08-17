DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:"
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django_custom_user_migration",
    "myapp",
]

SITE_ID = 1

MIDDLEWARE_CLASSES = []

SECRET_KEY = "abc"
