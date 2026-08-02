"""Configurações do SimaoFarma para SQLite local, Supabase e Vercel."""

import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Permite usar as variáveis baixadas com `vercel env pull .env.local`.
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.getenv("VERCEL"))

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if IS_VERCEL:
        raise RuntimeError(
            "A variável DJANGO_SECRET_KEY precisa ser configurada na Vercel."
        )
    SECRET_KEY = "django-insecure-apenas-para-desenvolvimento-local"

DEBUG = os.getenv(
    "DJANGO_DEBUG",
    "false" if IS_VERCEL else "true",
).lower() in {"1", "true", "yes", "on"}


def env_list(name: str) -> list[str]:
    """Lê uma variável separada por vírgulas e remove itens vazios."""
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".vercel.app"]
ALLOWED_HOSTS.extend(env_list("DJANGO_ALLOWED_HOSTS"))

CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]
CSRF_TRUSTED_ORIGINS.extend(env_list("DJANGO_CSRF_TRUSTED_ORIGINS"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'storages',
    'whitenoise.runserver_nostatic',
    "vendas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "comercio.urls"

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

WSGI_APPLICATION = "comercio.wsgi.application"


def get_database_url() -> tuple[str | None, str | None]:
    """Seleciona a conexão adequada para Vercel ou tarefas locais.

    DATABASE_URL e SUPABASE_DATABASE_URL funcionam como substituições explícitas.
    Pela integração Supabase da Vercel, POSTGRES_URL é a conexão agrupada usada
    no runtime, enquanto POSTGRES_URL_NON_POOLING é preferida localmente para
    migrações e importações.
    """
    explicit_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    if explicit_url:
        return explicit_url, "explícita"

    if IS_VERCEL:
        candidates = (
            ("POSTGRES_URL", os.getenv("POSTGRES_URL")),
            ("POSTGRES_URL_NON_POOLING", os.getenv("POSTGRES_URL_NON_POOLING")),
        )
    else:
        candidates = (
            ("POSTGRES_URL_NON_POOLING", os.getenv("POSTGRES_URL_NON_POOLING")),
            ("POSTGRES_URL", os.getenv("POSTGRES_URL")),
        )

    for source, value in candidates:
        if value:
            return value, source

    return None, None


DATABASE_URL, DATABASE_URL_SOURCE = get_database_url()

if DATABASE_URL:
    database_config = dj_database_url.parse(
        DATABASE_URL,
        # Functions serverless não devem manter conexões ociosas entre execuções.
        conn_max_age=0,
        conn_health_checks=True,
        ssl_require=True,
    )

    parsed_database_url = urlparse(DATABASE_URL)
    uses_transaction_pooler = parsed_database_url.port == 6543

    if uses_transaction_pooler:
        # O Transaction Pooler do Supabase não aceita prepared statements.
        # O Psycopg 3 permite desativá-los por conexão com prepare_threshold=None.
        database_config.setdefault("OPTIONS", {})["prepare_threshold"] = None

    # Evita cursores vinculados à sessão, incompatíveis com transaction pooling.
    database_config["DISABLE_SERVER_SIDE_CURSORS"] = True
    DATABASES = {"default": database_config}
else:
    if IS_VERCEL:
        raise RuntimeError(
            "Nenhuma URL PostgreSQL foi encontrada. Conecte a integração Supabase "
            "à Vercel ou configure DATABASE_URL/SUPABASE_DATABASE_URL."
        )
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
        "endpoint_url": os.getenv('SUPABASE_S3_ENDPOINT'),
        "access_key": os.getenv('SUPABASE_S3_ACCESS_KEY'),
        "secret_key": os.getenv('SUPABASE_S3_SECRET_KEY'),
        "bucket_name": os.getenv('SUPABASE_S3_BUCKET_NAME'),
        "region_name": os.getenv('SUPABASE_REGION', 'sa-east-1'),
        "default_acl": "public-read",
    },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = IS_VERCEL
SESSION_COOKIE_SECURE = IS_VERCEL

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
