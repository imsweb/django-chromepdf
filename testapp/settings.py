import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'chromepdf_tests_secret'

INSTALLED_APPS = [
    'chromepdf',
    'testapp',
]

WSGI_APPLICATION = 'testapp.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
