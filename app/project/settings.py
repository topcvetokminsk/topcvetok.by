import logging.config
import os

from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = int(os.environ.get("DEBUG", 1))

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED", "").split(",")

# This can be dangerous, be aware!
os.environ.setdefault("C_FORCE_ROOT", "true")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_db_comments",
    # THIRD PARTY
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # APPS
    "topcvetok",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATE_INPUT_FORMATS": ["%d.%m.%Y"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "project.paginators.LimitPagination",
    "COERCE_DECIMAL_TO_STRING": False,
    'NON_FIELD_ERRORS_KEY': 'errorMessage',
}

SPECTACULAR_SETTINGS = {
    "TITLE": "TopCvetok API",
    "DESCRIPTION": "Документация",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    "SERVE_INCLUDE_SCHEMA": False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'SERVE_AUTHENTICATION': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        },
    },
    'SECURITY': [{'Bearer': []}],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers ": True,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "console_for_request": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "request_formatter",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console_for_request"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname}: {name} {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
        "request_formatter": {
            "format": (
                "[{asctime}] {levelname}: {request.META[REMOTE_ADDR]} "
                "{request.META[REQUEST_METHOD]} {request.path} {status_code}"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
}

logging.config.dictConfig(LOGGING)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CLIENT_CLASS": "django_redis.client.HerdClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,  # Еще меньше для 2GB RAM сервера
                "retry_on_timeout": True,
                "socket_keepalive": True,
                "socket_keepalive_options": {},
            },
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "Session",
        'MAX_ENTRIES': 2000,  # Еще меньше для экономии памяти
        'TIMEOUT': 300,  # 5 минут
    }
}

# Celery Configuration Options
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = "Europe/Minsk"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SERIALIZER = "json"  # Безопаснее чем pickle
CELERY_ACCEPT_CONTENT = ["json"]  # Убрано pickle
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Оптимизации Celery для малого сервера (2GB RAM, 2 CPU)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Один таск на воркер
CELERY_TASK_ACKS_LATE = True  # Подтверждение после выполнения
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_CONCURRENCY = 2  # 2 воркера для 2 CPU
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50  # Перезапуск воркеров для экономии памяти

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = bool(os.environ.get("SMTP_USE_TLS", False))
EMAIL_HOST = os.environ.get("SMTP_HOST")
EMAIL_PORT = int(os.environ.get("SMTP_PORT"))
EMAIL_HOST_USER = os.environ.get("SMTP_USER")
EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD")

# CONFIG CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF_FAILURE_VIEW = "core.csrf.csrf_failure"
# CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED", "").split(",")
# CSRF_HEADER_NAME = "CSRF_COOKIE"

# CONFIG PROD SECURE
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    #CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    
    # Дополнительные оптимизации для продакшена
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Оптимизация логирования для продакшена
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "file": {
                "level": "WARNING",
                "class": "logging.FileHandler",
                "filename": "/var/log/django/error.log",
            },
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["file", "console"],
            "level": "WARNING",
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }


ROOT_URLCONF = "project.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DB_NAME", "cvetok"),
        "USER": os.environ.get("DB_USER", "cvetok"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "cvetok"),
        "HOST": os.environ.get("DB_HOST", "172.17.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "options": "-c search_path=django,public", 
            "application_name": "topcvetok_django"
        },
        # Оптимизации для производительности
        "CONN_MAX_AGE": 600,  # 10 минут
        "CONN_HEALTH_CHECKS": True,
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# Оптимизации для малого сервера
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB - ограничение размера файлов
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB - ограничение размера данных

# Настройки сессий для экономии памяти
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 3600  # 1 час


# AUTH CONFIGURATION
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_LIFETIME", 10))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("REFRESH_TOKEN_LIFETIME", 60))),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "SLIDING_TOKEN_LIFETIME": timedelta(days=1),
    "SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER": timedelta(days=1),
    "SLIDING_TOKEN_LIFETIME_LATE_USER": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

AUTH_USER_MODEL = "topcvetok.Account"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "topcvetok.validators.PasswordValidator"},
]


# TIME AND LANGUAGE
LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Europe/Minsk"
USE_I18N = True
USE_L10N = True
USE_TZ = True

EMAIL_TO = os.getenv('EMAIL_TO')


# Static and Media storage settings
PROJECT_DIR = os.path.dirname(__file__)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static/')

MEDIA_URL = os.getenv("MEDIA_URL")

FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
FTP_PORT = os.environ.get("FTP_PORT")
FTP_HOST = os.environ.get("FTP_HOST")

DEFAULT_FILE_STORAGE = 'storages.backends.ftp.FTPStorage'
FTP_STORAGE_LOCATION = 'ftps://' + FTP_USER + ':' + FTP_PASS + f'@{FTP_HOST}:' + FTP_PORT + "/"
FTP_STORAGE_ENCODING = "utf-8"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
