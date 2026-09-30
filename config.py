import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def generate_secret_key():
    """Generate a secure random secret key if not provided"""
    return os.environ.get('SECRET_KEY') or secrets.token_hex(32)

def generate_jwt_secret():
    """Generate a secure JWT secret key if not provided"""
    return os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)

class Config:
    # Flask
    SECRET_KEY = generate_secret_key()
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    SERVER_NAME = os.environ.get('SERVER_NAME')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///casino.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Security
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 12))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))

    # JWT
    JWT_SECRET_KEY = generate_jwt_secret()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 86400)))

    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per minute')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Payment Gateways - Whish Money (Lebanon)
    WHISH_CHANNEL = os.environ.get('WHISH_CHANNEL')
    WHISH_SECRET = os.environ.get('WHISH_SECRET')
    WHISH_WEBSITE_URL = os.environ.get('WHISH_WEBSITE_URL')
    WHISH_BASE_URL = os.environ.get('WHISH_BASE_URL', 'https://whish.money/itel-service/api')
    WHISH_WEBHOOK_SECRET = os.environ.get('WHISH_WEBHOOK_SECRET')
    WHISH_SANDBOX = os.environ.get('WHISH_SANDBOX', 'false').lower() == 'true'

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@jsrush.com')

    # WhatsApp Contact for Manual Deposits/Withdrawals
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '96171903956')

    # Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))

    # Login Security
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOGIN_LOCKOUT_DURATION = int(os.environ.get('LOGIN_LOCKOUT_DURATION', 900))  # 15 minutes
    EMAIL_VERIFICATION_REQUIRED = os.environ.get('EMAIL_VERIFICATION_REQUIRED', 'true').lower() == 'true'
    PHONE_VERIFICATION_REQUIRED = os.environ.get('PHONE_VERIFICATION_REQUIRED', 'false').lower() == 'true'
    LOGIN_NOTIFICATION_EMAIL = os.environ.get('LOGIN_NOTIFICATION_EMAIL', 'true').lower() == 'true'
    TRUSTED_DEVICES_ENABLED = os.environ.get('TRUSTED_DEVICES_ENABLED', 'true').lower() == 'true'
    
    # 2FA Configuration
    TWO_FA_REQUIRED_FOR_ADMIN = os.environ.get('TWO_FA_REQUIRED_FOR_ADMIN', 'true').lower() == 'true'
    TWO_FA_ISSUER_NAME = os.environ.get('TWO_FA_ISSUER_NAME', 'JS Rush')
    
    # Security Headers
    SECURE_HEADERS_ENABLED = os.environ.get('SECURE_HEADERS_ENABLED', 'true').lower() == 'true'
    HSTS_MAX_AGE = int(os.environ.get('HSTS_MAX_AGE', 31536000))  # 1 year
    CSP_ENABLED = os.environ.get('CSP_ENABLED', 'true').lower() == 'true'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    
    # Content Security Policy
    CSP_POLICY = os.environ.get('CSP_POLICY', "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.whish.money https://api.paystack.co https://api.flutterwave.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per minute')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    RATELIMIT_HEADERS_ENABLED = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))
    
    # Sentry
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', 0.1))
    
    # Prometheus Metrics
    PROMETHEUS_METRICS_ENABLED = os.environ.get('PROMETHEUS_METRICS_ENABLED', 'true').lower() == 'true'
    PROMETHEUS_METRICS_PATH = '/metrics'
    
    # Backup Configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    BACKUP_S3_BUCKET = os.environ.get('BACKUP_S3_BUCKET')
    BACKUP_S3_REGION = os.environ.get('BACKUP_S3_REGION', 'us-east-1')
    BACKUP_S3_ACCESS_KEY = os.environ.get('BACKUP_S3_ACCESS_KEY')
    BACKUP_S3_SECRET_KEY = os.environ.get('BACKUP_S3_SECRET_KEY')
    
    # Disaster Recovery
    DR_ENABLED = os.environ.get('DR_ENABLED', 'false').lower() == 'true'
    DR_RPO_MINUTES = int(os.environ.get('DR_RPO_MINUTES', 60))
    DR_RTO_MINUTES = int(os.environ.get('DR_RTO_MINUTES', 240))
    
    # Admin Security
    ADMIN_IP_WHITELIST = os.environ.get('ADMIN_IP_WHITELIST', '').split(',') if os.environ.get('ADMIN_IP_WHITELIST') else []
    ADMIN_2FA_REQUIRED = os.environ.get('ADMIN_2FA_REQUIRED', 'true').lower() == 'true'
    
    # Currency
    SUPPORTED_CURRENCIES = ['USD', 'LBP', 'AED']
    DEFAULT_CURRENCY = 'USD'

    # Gambling Compliance (USD amounts for Lebanon)
    MIN_DEPOSIT = float(os.environ.get('MIN_DEPOSIT', 10))
    MAX_DEPOSIT = float(os.environ.get('MAX_DEPOSIT', 10000))
    MIN_WITHDRAWAL = float(os.environ.get('MIN_WITHDRAWAL', 20))
    MAX_WITHDRAWAL = float(os.environ.get('MAX_WITHDRAWAL', 5000))
    DAILY_DEPOSIT_LIMIT = float(os.environ.get('DAILY_DEPOSIT_LIMIT', 5000))
    DAILY_WITHDRAWAL_LIMIT = float(os.environ.get('DAILY_WITHDRAWAL_LIMIT', 2000))
    KYC_REQUIRED_AMOUNT = float(os.environ.get('KYC_REQUIRED_AMOUNT', 2000))

    # Responsible Gambling
    DEFAULT_DAILY_DEPOSIT_LIMIT = float(os.environ.get('DEFAULT_DAILY_DEPOSIT_LIMIT', 500))
    DEFAULT_DAILY_LOSS_LIMIT = float(os.environ.get('DEFAULT_DAILY_LOSS_LIMIT', 200))
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 1800))

    KYC_REQUIRED_AMOUNT = float(os.environ.get('KYC_REQUIRED_AMOUNT', 2000))

    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@jsrush.com')

    # Frontend URL (for CORS)
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://jsrush.com')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    SENTRY_DSN = os.environ.get('SENTRY_DSN')

    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/2')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')

    # Supported currencies
    SUPPORTED_CURRENCIES = ['USD', 'LBP', 'AED']
    DEFAULT_CURRENCY = 'USD'
    
    # Currency-specific limits (in base currency units)
    CURRENCY_LIMITS = {
        'USD': {
            'min_deposit': 10, 'max_deposit': 10000,
            'min_withdrawal': 20, 'max_withdrawal': 5000,
            'daily_deposit_limit': 5000, 'daily_withdrawal_limit': 2000,
            'kyc_required': 2000
        },
        'LBP': {
            'min_deposit': 150000, 'max_deposit': 150000000,
            'min_withdrawal': 300000, 'max_withdrawal': 75000000,
            'daily_deposit_limit': 75000000, 'daily_withdrawal_limit': 30000000,
            'kyc_required': 30000000
        },
        'AED': {
            'min_deposit': 37, 'max_deposit': 36700,
            'min_withdrawal': 74, 'max_withdrawal': 18350,
            'daily_deposit_limit': 18350, 'daily_withdrawal_limit': 7340,
            'kyc_required': 7340
        }
    }


class DevelopmentConfig(Config):
    FLASK_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///casino.db')
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    FLASK_DEBUG = False
    # PostgreSQL required for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    BCRYPT_ROUNDS = 4


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}