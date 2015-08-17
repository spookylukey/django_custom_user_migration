DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tests.db"
    }
}

INSTALLED_APPS = [
    # INSTALLED_APPS_start
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "myapp",
    # INSTALLED_APPS_end
]

SITE_ID = 1

MIDDLEWARE_CLASSES = []

SECRET_KEY = "abc"
