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
    'compras',
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
        lambda request: static("admin/css/barrs_premium.css"),
    ],
    "SCRIPTS": [],

    # Paleta de cores convertida para oklch — cinza neutro premium
    "COLORS": {
        # Neutros: escala cinza fria — Linear/Stripe style
        "base": {
            "50":  "oklch(98.2% 0.002 256)",   # #F9FAFB — fundo geral
            "100": "oklch(96.3% 0.003 256)",   # #F3F4F6
            "200": "oklch(92.4% 0.004 256)",   # #E5E7EB — bordas
            "300": "oklch(87.2% 0.006 256)",   # #D1D5DB
            "400": "oklch(71.0% 0.007 256)",   # #9CA3AF — placeholder
            "500": "oklch(55.8% 0.008 256)",   # #6B7280 — muted
            "600": "oklch(43.8% 0.006 256)",   # #4B5563
            "700": "oklch(36.4% 0.005 256)",   # #374151 — texto secundário
            "800": "oklch(26.0% 0.004 256)",   # #1F2937
            "900": "oklch(18.5% 0.003 256)",   # #111827 — texto principal
            "950": "oklch(12.0% 0.002 256)",   # #0F172A — sidebar
        },
        # Primário: verde floresta — mais escuro e autoritativo
        "primary": {
            "50":  "oklch(97.2% 0.020 143)",   # fundo verde suave
            "100": "oklch(93.4% 0.042 143)",
            "200": "oklch(87.8% 0.068 143)",
            "300": "oklch(80.4% 0.090 143)",
            "400": "oklch(70.0% 0.112 143)",
            "500": "oklch(58.0% 0.122 143)",   # verde médio
            "600": "oklch(47.4% 0.106 143)",   # #3D6B22 — primário forte
            "700": "oklch(38.0% 0.086 143)",   # #2E5219 — primário escuro
            "800": "oklch(29.5% 0.066 143)",
            "900": "oklch(21.8% 0.048 143)",
            "950": "oklch(15.0% 0.033 143)",
        },
        "font": {
            "subtle-light":    "var(--color-base-500)",  # muted
            "subtle-dark":     "var(--color-base-400)",
            "default-light":   "var(--color-base-900)",  # alto contraste
            "default-dark":    "var(--color-base-200)",
            "important-light": "var(--color-base-950)",  # títulos máximo contraste
            "important-dark":  "var(--color-base-50)",
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
                        "icon": "orders",
                        "link": reverse_lazy("admin:pedidos_pedido_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Devoluções",
                        "icon": "assignment_returned",
                        "link": reverse_lazy("admin:pedidos_devolucao_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Produtos",
                        "icon": "inventory",
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
                        "icon": "groups",
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
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:financeiro_contareceber_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Contas a Pagar",
                        "icon": "request_quote",
                        "link": reverse_lazy("admin:financeiro_contapagar_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Lançamentos de Caixa",
                        "icon": "payments",
                        "link": reverse_lazy("admin:financeiro_lancamentocaixa_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Categorias Financeiras",
                        "icon": "category",
                        "link": reverse_lazy("admin:financeiro_categoriafinanceira_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Fornecedores",
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:produtos_fornecedor_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Pedidos de Compra",
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:compras_pedidocompra_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": "Recebimentos",
                        "icon": "inventory",
                        "link": reverse_lazy("admin:compras_recebimentomercadoria_changelist"),
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
