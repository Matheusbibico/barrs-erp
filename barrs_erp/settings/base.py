from pathlib import Path
from decouple import config
import dj_database_url
from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # Unfold deve vir antes de django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'produtos',
    'clientes',
    'pedidos',
    'estoque',
    'financeiro',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'barrs_erp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'barrs_erp.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3'),
        conn_max_age=600,
    )
}

_site_db_url = config('SITE_DATABASE_URL', default='')
if _site_db_url:
    DATABASES['site'] = dj_database_url.parse(_site_db_url, conn_max_age=60)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

WEBHOOK_TOKEN = config('WEBHOOK_TOKEN', default='')

# ─── Unfold Admin ────────────────────────────────────────────────────────────
# Paleta Barrs: neutros quentes (bege/marrom) + verde primário
# Cores em oklch (Oklab Lightness Chroma Hue) — formato exigido pelo Unfold 0.90+
UNFOLD = {
    "SITE_TITLE": "Barrs ERP",
    "SITE_HEADER": "Barrs Store",
    "SITE_SUBHEADER": "Gestão interna",
    "SITE_URL": "/",
    "SITE_ICON": None,
    "SITE_SYMBOL": "storefront",  # Google Material icon
    "SITE_LOGO": None,
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    "THEME": "light",  # força tema light como padrão (persiste em localStorage)

    # Callback que injeta estatísticas na página inicial do admin
    "DASHBOARD_CALLBACK": "core.admin.dashboard.dashboard_callback",

    # CSS customizado carregado após o CSS do Unfold
    "STYLES": [
        lambda request: static("admin/css/barrs_admin.css"),
    ],
    "SCRIPTS": [
        lambda request: static("admin/js/barrs_force_light.js"),
    ],

    # Paleta de cores da Barrs convertida para oklch
    "COLORS": {
        # Neutros: escala de bege quente → marrom escuro
        "base": {
            "50":  "oklch(99.1% 0.003 84.6)",   # quase branco aquecido
            "100": "oklch(96.2% 0.009 84.6)",   # #F5F2EC — fundo principal
            "200": "oklch(92.6% 0.014 84.6)",   # #EBE6DC
            "300": "oklch(86.8% 0.018 84.6)",   # #D9D3C7 — bordas
            "400": "oklch(79.3% 0.017 73.6)",   # cinza-bege médio
            "500": "oklch(67.2% 0.021 72.5)",   # #9E9488 — texto muted
            "600": "oklch(56.4% 0.021 75.2)",   # tom médio
            "700": "oklch(49.1% 0.024 62.5)",   # #6B5E53 — texto principal
            "800": "oklch(39.9% 0.016 48.3)",   # escuro
            "900": "oklch(30.7% 0.012 51.7)",   # muito escuro
            "950": "oklch(22.2% 0.007 48.4)",   # quase preto
        },
        # Primário: escala do verde Barrs #8A947C
        "primary": {
            "50":  "oklch(94.0% 0.014 128.6)",  # #E8EDE3 — fundo verde
            "100": "oklch(89.7% 0.023 126.3)",
            "200": "oklch(84.1% 0.036 130.5)",
            "300": "oklch(79.6% 0.036 125.0)",  # #B7C1A8 — verde claro
            "400": "oklch(71.9% 0.046 126.1)",
            "500": "oklch(65.2% 0.037 125.8)",  # #8A947C — verde primário
            "600": "oklch(57.1% 0.036 126.7)",
            "700": "oklch(48.9% 0.033 127.3)",
            "800": "oklch(40.8% 0.029 128.2)",
            "900": "oklch(32.6% 0.026 129.4)",
            "950": "oklch(24.8% 0.018 131.4)",
        },
        "font": {
            "subtle-light":    "var(--color-base-500)",  # texto muted
            "subtle-dark":     "var(--color-base-400)",
            "default-light":   "var(--color-base-700)",  # texto principal
            "default-dark":    "var(--color-base-300)",
            "important-light": "var(--color-base-900)",  # títulos
            "important-dark":  "var(--color-base-100)",
        },
    },

    # Barra lateral com grupos lógicos do ERP
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Loja",
                "separator": False,
                "collapsible": False,
                "items": [
                    {
                        "title": "Pedidos",
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:pedidos_pedido_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Devoluções",
                        "icon": "assignment_return",
                        "link": reverse_lazy("admin:pedidos_devolucao_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Produtos",
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:produtos_produto_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Categorias",
                        "icon": "label",
                        "link": reverse_lazy("admin:produtos_categoria_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Clientes",
                        "icon": "people",
                        "link": reverse_lazy("admin:clientes_cliente_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                ],
            },
            {
                "title": "Operações",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Movimentos de Estoque",
                        "icon": "warehouse",
                        "link": reverse_lazy("admin:estoque_movimentoestoque_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Contas a Receber",
                        "icon": "payments",
                        "link": reverse_lazy("admin:financeiro_contareceber_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Contas a Pagar",
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:financeiro_contapagar_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Fornecedores",
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:produtos_fornecedor_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                ],
            },
            {
                "title": "Sistema",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Grupos",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Logs de Atividade",
                        "icon": "history",
                        "link": reverse_lazy("admin:admin_logentry_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },

    "TABS": [],
}
