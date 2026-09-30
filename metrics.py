from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from flask import request, g
import time
import functools

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

http_response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Business Metrics
active_users = Gauge(
    'active_users',
    'Number of currently active users'
)

total_users = Gauge(
    'total_users',
    'Total registered users'
)

user_balance_total = Gauge(
    'user_balance_total',
    'Total user balances in NGN'
)

deposits_total = Counter(
    'deposits_total',
    'Total deposits',
    ['gateway', 'currency']
)

deposits_amount = Counter(
    'deposits_amount_ngn',
    'Total deposit amount in NGN',
    ['gateway']
)

withdrawals_total = Counter(
    'withdrawals_total',
    'Total withdrawals',
    ['gateway', 'currency']
)

withdrawals_amount = Counter(
    'withdrawals_amount_ngn',
    'Total withdrawal amount in NGN',
    ['gateway']
)

game_bets_total = Counter(
    'game_bets_total',
    'Total game bets placed',
    ['game_type']
)

game_wins_total = Counter(
    'game_wins_total',
    'Total game wins',
    ['game_type']
)

game_bet_amount = Counter(
    'game_bet_amount_ngn',
    'Total bet amount in NGN',
    ['game_type']
)

game_win_amount = Counter(
    'game_win_amount_ngn',
    'Total win amount in NGN',
    ['game_type']
)

game_duration = Histogram(
    'game_duration_seconds',
    'Game session duration in seconds',
    ['game_type'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

# User Metrics
user_registrations = Counter(
    'user_registrations_total',
    'Total user registrations'
)

user_logins = Counter(
    'user_logins_total',
    'Total user logins'
)

user_verifications = Counter(
    'user_verifications_total',
    'Total email verifications',
    ['method']  # email, phone
)

user_kyc_submissions = Counter(
    'user_kyc_submissions_total',
    'Total KYC submissions',
    ['status']  # submitted, approved, rejected
)

user_2fa_enabled = Counter(
    'user_2fa_enabled_total',
    'Total 2FA enabled'
)

# Responsible Gambling Metrics
self_exclusions = Counter(
    'self_exclusions_total',
    'Total self-exclusions',
    ['type']  # permanent, temporary
)

cool_offs = Counter(
    'cool_offs_total',
    'Total cool-off periods'
)

deposit_limit_changes = Counter(
    'deposit_limit_changes_total',
    'Deposit limit changes'
)

loss_limit_changes = Counter(
    'loss_limit_changes_total',
    'Loss limit changes'
)

# Transaction Metrics
transaction_amount = Histogram(
    'transaction_amount_ngn',
    'Transaction amounts in NGN',
    ['type'],  # deposit, withdraw, game, admin
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]
)

transaction_duration = Histogram(
    'transaction_duration_seconds',
    'Transaction processing duration',
    ['type', 'gateway'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Payment Gateway Metrics
payment_gateway_requests = Counter(
    'payment_gateway_requests_total',
    'Payment gateway API requests',
    ['gateway', 'endpoint', 'status']
)

payment_gateway_latency = Histogram(
    'payment_gateway_latency_seconds',
    'Payment gateway API latency',
    ['gateway', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Database Metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

db_connections = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_pool_usage = Gauge(
    'db_pool_usage_percent',
    'Database connection pool usage percent'
)

# Redis Metrics
redis_connections = Gauge(
    'redis_connections_active',
    'Active Redis connections'
)

redis_memory = Gauge(
    'redis_memory_bytes',
    'Redis memory usage in bytes'
)

redis_commands = Counter(
    'redis_commands_total',
    'Redis commands executed',
    ['command']
)

# Celery Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # success, failure, retry
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 60.0, 300.0, 600.0]
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Celery queue length',
    ['queue']
)

celery_workers = Gauge(
    'celery_workers_active',
    'Active Celery workers'
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['type', 'endpoint']
)

# Security Metrics
failed_logins = Counter(
    'failed_logins_total',
    'Failed login attempts',
    ['reason']  # invalid_password, locked_account, invalid_2fa
)

blocked_ips = Gauge(
    'blocked_ips_total',
    'Currently blocked IPs'
)

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Rate limit exceeded',
    ['endpoint']
)


def init_metrics(app):
    """Initialize Prometheus metrics for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_start = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            http_request_duration.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
            
            http_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
            
            # Request/response size
            if request.content_length:
                http_request_size.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(request.content_length)
            
            response_size = len(response.get_data())
            if response_size:
                http_response_size.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(response_size)
        
        return response
    
    @app.route('/metrics')
    def metrics():
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    return app


# Helper functions for recording metrics
def record_deposit(gateway, amount, currency='NGN'):
    deposits_total.labels(gateway=gateway, currency=currency).inc()
    deposits_amount.labels(gateway=gateway).inc(amount)


def record_withdrawal(gateway, amount, currency='NGN'):
    withdrawals_total.labels(gateway=gateway, currency=currency).inc()
    withdrawals_amount.labels(gateway=gateway).inc(amount)


def record_game_bet(game_type, amount):
    game_bets_total.labels(game_type=game_type).inc()
    game_bet_amount.labels(game_type=game_type).inc(amount)


def record_game_win(game_type, amount):
    game_wins_total.labels(game_type=game_type).inc()
    game_win_amount.labels(game_type=game_type).inc(amount)


def record_game_duration(game_type, duration):
    game_duration.labels(game_type=game_type).observe(duration)


def record_user_registration():
    user_registrations.inc()


def record_user_login():
    user_logins.inc()


def record_email_verification(method='email'):
    user_verifications.labels(method=method).inc()


def record_kyc_submission(status):
    user_kyc_submissions.labels(status=status).inc()


def record_2fa_enabled():
    user_2fa_enabled.inc()


def record_self_exclusion(exclusion_type):
    self_exclusions.labels(type=exclusion_type).inc()


def record_cool_off():
    cool_offs.inc()


def record_deposit_limit_change():
    deposit_limit_changes.inc()


def record_loss_limit_change():
    loss_limit_changes.inc()


def record_failed_login(reason):
    failed_logins.labels(reason=reason).inc()


def record_rate_limit_exceeded(endpoint):
    rate_limit_exceeded.labels(endpoint=endpoint).inc()


def record_payment_gateway_request(gateway, endpoint, status):
    payment_gateway_requests.labels(gateway=gateway, endpoint=endpoint, status=status).inc()


def record_payment_gateway_latency(gateway, endpoint, duration):
    payment_gateway_latency.labels(gateway=gateway, endpoint=endpoint).observe(duration)


def record_db_query(query_type, duration):
    db_query_duration.labels(query_type=query_type).observe(duration)


def record_celery_task(task_name, status, duration=None):
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    if duration is not None:
        celery_task_duration.labels(task_name=task_name).observe(duration)


def record_error(error_type, endpoint):
    errors_total.labels(type=error_type, endpoint=endpoint).inc()