from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']
MEDIA_ROOT = '/var/opt/hackergame/media'
STATIC_ROOT = '/var/opt/hackergame/static'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db',
        'NAME': 'hackergame',
        'USER': 'hackergame',
        'PASSWORD': 'hackergame',
        'CONN_MAX_AGE': 60,
        'ATOMIC_REQUESTS': True,
    },
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 3600,
        'KEY_PREFIX': 'hackergame',
    },
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.s.ustclug.org'

GOOGLE_APP_ID = '2574063612-kstsrirbttbimgk2da2ju1mmbh8t0ogk' \
                '.apps.googleusercontent.com'
MICROSOFT_APP_ID = '6a243fe9-a603-4c6e-b6bd-5af20b7f460e'
SMS_ACCESS_KEY_ID = 'LTAI4FmgeKHNWB7WbTwTP7d9'
