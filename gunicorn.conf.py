import os

port = os.environ.get('PORT', '8000')
bind = f"0.0.0.0:{port}"
workers = int(os.environ.get('GUNICORN_WORKERS', '4'))
worker_class = 'gevent'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_fields = 100
limit_request_field_size = 8190
limit_request_line = 4094

# Process naming
proc_name = 'jsrush'

# Preload
preload_app = True

# Worker tmp dir
worker_tmp_dir = '/dev/shm'