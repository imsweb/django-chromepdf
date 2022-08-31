import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TESTAPP_DIR = os.path.join(BASE_DIR, 'testapp')
TEMP_DIR = os.path.join(TESTAPP_DIR, 'temp')

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
