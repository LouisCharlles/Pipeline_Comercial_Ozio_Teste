"""Configuração do backend.

Tudo vem de variáveis de ambiente; os padrões batem com o docker-compose.yml para que o ambiente
local funcione sem nenhum .env.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(nome: str, padrao: bool) -> bool:
    return os.environ.get(nome, str(padrao)).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao")
DEBUG = _bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "comercial",
]

# A API não tem login nem sessão e só é chamada pelo servidor Node do frontend.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "pipeline"),
        "USER": os.environ.get("POSTGRES_USER", "pipeline"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "pipeline"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "comercial.erros.tratar_excecao",
}

# Integração com o ERP (simulado). Ver specs/001-pipeline-comercial-erp/research.md, R4.
ERP_MODO = os.environ.get("ERP_MODO", "sucesso")
ERP_LATENCIA_MS = int(os.environ.get("ERP_LATENCIA_MS", "0"))
ERP_TIMEOUT_SEGUNDOS = int(os.environ.get("ERP_TIMEOUT_SEGUNDOS", "5"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simples": {"format": "{levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simples"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}
