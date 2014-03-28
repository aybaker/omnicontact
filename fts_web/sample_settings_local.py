# -*- coding: utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

MEDIA_ROOT = '/home/username/ftsenderweb/media_files/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ftsenderweb_db',
        'USER': 'ftsenderweb',
        'PASSWORD': 'XXXXXXXXX',
        'HOST': 'localhost',
        'PORT': '',
    }
}

SELENIUM_WEBDRIVER_BIN = (
    # Ubuntu 13.04 / Ubuntu 13.10 - Package: 'chromium-chromedriver'
    '/usr/lib/chromium-browser/chromedriver',
)
