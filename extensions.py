from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint, google
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
import redis

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# In-memory rate limiter storage (no Redis required)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)

mail = Mail()
migrate = Migrate()

# Simple in-memory cache fallback (no Redis required)
class SimpleCache:
    """Simple in-memory cache fallback when Redis is unavailable"""
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key):
        import time
        if key in self._cache:
            if key in self._expiry and self._expiry[key] < time.time():
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    def set(self, key, value, ex=None):
        import time
        self._cache[key] = value
        if ex:
            self._expiry[key] = time.time() + ex
        else:
            self._expiry[key] = None
    
    def delete(self, key):
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def setex(self, key, time, value):
        self.set(key, value, ex=time)
    
    def incr(self, key):
        val = self.get(key) or 0
        val = int(val) + 1
        self.set(key, str(val))
        return val
    
    def expire(self, key, seconds):
        import time
        if key in self._cache:
            self._expiry[key] = time.time() + seconds

redis_client = None

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Rate limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)

mail = Mail()
migrate = Migrate()
talisman = Talisman()
csrf = CSRFProtect()

# Simple in-memory cache fallback (no Redis required)
class SimpleCache:
    """Simple in-memory cache fallback when Redis is unavailable"""
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key):
        import time
        if key in self._cache:
            if key in self._expiry and self._expiry[key] < time.time():
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    def set(self, key, value, ex=None):
        import time
        self._cache[key] = value
        if ex:
            self._expiry[key] = time.time() + ex
        else:
            self._expiry[key] = None
    
    def delete(self, key):
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def setex(self, key, time, value):
        self.set(key, value, ex=time)
    
    def incr(self, key):
        val = self.get(key) or 0
        val = int(val) + 1
        self.set(key, str(val))
        return val
    
    def expire(self, key, seconds):
        import time
        if key in self._cache:
            self._expiry[key] = time.time() + seconds

redis_client = None
csrf_exempt_routes = set()

def init_extensions(app):
    global redis_client
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    talisman.init_app(app)
    csrf.init_app(app)
    
    # Initialize CSRF exempt routes
    global csrf_exempt_routes
    csrf_exempt_routes = {
        '/webhook/whish',
        '/webhook/whish/callback',
        '/webhook/whish',
        '/webhook/paystack',
        '/webhook/flutterwave',
        '/webhook/monnify',
        '/webhook/whish/callback',
    }
    
    # Setup CSRF exemption for webhook routes
    @csrf.exempt
    def csrf_exempt_check():
        pass
    
    @app.before_request
    def csrf_protect_exempt():
        if request.path in csrf_exempt_routes:
            return None
        return None
    
    # Setup Google OAuth
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        google_bp = make_google_blueprint(
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            scope=['openid', 'email', 'profile'],
            redirect_to='auth.google_authorized'
        )
        app.register_blueprint(google_bp, url_prefix='/auth')
    
    # Initialize Talisman for security headers
    if app.config.get('SECURE_HEADERS_ENABLED', True):
        talisman.init_app(
            app,
            force_https=app.config.get('SESSION_COOKIE_SECURE', True),
            strict_transport_security=app.config.get('HSTS_MAX_AGE', 31536000),
            strict_transport_security_preload=True,
            session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', True),
            session_cookie_http_only=True,
            session_cookie_samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            content_security_policy=app.config.get('CSP_POLICY') if app.config.get('CSP_ENABLED') else None,
            referrer_policy='strict-origin-when-cross-origin',
            permissions_policy={
                'geolocation': "'none'",
                'camera': "'none'",
                'microphone': "'none'",
                'payment': "'self'"
            },
            frame_options='DENY',
            x_content_type_options='nosniff',
            x_xss_protection='1; mode=block'
        )
    
    # Initialize CSRF
    csrf.init_app(app)
    
    # CSRF exemption for webhook routes
    @app.before_request
    def csrf_protect_exempt():
        from flask import request
        if request.path in csrf_exempt_routes:
            csrf = CSRFProtect()
            csrf._exempt_views.add(request.endpoint)
        return None
    
    # Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        if app.config.get('SECURE_HEADERS_ENABLED', True):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=(), payment=(self)'
            
            # HSTS
            if app.config.get('SESSION_COOKIE_SECURE', True):
                response.headers['Strict-Transport-Security'] = f'max-age={app.config.get("HSTS_MAX_AGE", 31536000)}; includeSubDomains; preload'
            
            # CSP
            if app.config.get('CSP_ENABLED', True) and app.config.get('CSP_POLICY'):
                response.headers['Content-Security-Policy'] = app.config['CSP_POLICY']
            
            # CORS headers for API
            if request.path.startswith('/api/'):
                origin = request.headers.get('Origin')
                if origin in app.config.get('CORS_ORIGINS', []):
                    response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    # Rate limiting headers
    @app.after_request
    def add_rate_limit_headers(response):
        if app.config.get('RATELIMIT_HEADERS_ENABLED', True):
            # Rate limit headers are added by flask-limiter
            pass
        return response
    
    # Prometheus metrics endpoint
    if app.config.get('PROMETHEUS_METRICS_ENABLED', True):
        @app.route(app.config.get('PROMETHEUS_METRICS_PATH', '/metrics'))
        def metrics():
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    
    return redis_client