"""
CSRF Protection for Flask
Custom CSRF protection without Flask-WTF dependency
"""
import secrets
import hmac
import hashlib
from functools import wraps
from flask import request, session, jsonify, current_app
from datetime import datetime, timedelta

class CSRFProtect:
    """CSRF Protection for Flask applications"""
    
    def __init__(self, app=None):
        self.app = app
        self._exempt_views = set()
        self._exempt_blueprints = set()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize CSRF protection for Flask app"""
        app.config.setdefault('WTF_CSRF_ENABLED', True)
        app.config.setdefault('WTF_CSRF_TIME_LIMIT', 3600)  # 1 hour
        app.config.setdefault('WTF_CSRF_SSL_STRICT', True)
        app.config.setdefault('WTF_CSRF_CHECK_DEFAULT', True)
        app.config.setdefault('WTF_CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])
        app.config.setdefault('WTF_CSRF_FIELD_NAME', 'csrf_token')
        app.config.setdefault('WTF_CSRF_HEADER_NAME', 'X-CSRFToken')
        
        # Store config
        self.app = app
        
        # Register before_request handler
        app.before_request(self._check_csrf)
        
        # Add template global for CSRF token
        app.jinja_env.globals['csrf_token'] = self.generate_csrf_token
        app.jinja_env.globals['csrf_input'] = self.csrf_input
        
        # Add context processor for templates
        @app.context_processor
        def inject_csrf():
            return {
                'csrf_token': self.generate_csrf_token,
                'csrf_input': self.csrf_input
            }
    
    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token and store in session"""
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
            session['_csrf_token_time'] = datetime.utcnow().isoformat()
        
        # Check token age
        token_time = datetime.fromisoformat(session.get('_csrf_token_time', datetime.utcnow().isoformat()))
        if datetime.utcnow() - token_time > timedelta(seconds=current_app.config.get('WTF_CSRF_TIME_LIMIT', 3600)):
            # Token expired, generate new one
            session['_csrf_token'] = secrets.token_hex(32)
            session['_csrf_token_time'] = datetime.utcnow().isoformat()
        
        return session['_csrf_token']
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token against session"""
        if not token:
            return False
        
        session_token = session.get('_csrf_token')
        if not session_token:
            return False
        
        # Constant-time comparison
        return hmac.compare_digest(token, session_token)
    
    def csrf_input(self) -> str:
        """Generate HTML input for CSRF token"""
        token = self.generate_csrf_token()
        return f'<input type="hidden" name="csrf_token" value="{token}">'
    
    def _check_csrf(self):
        """Check CSRF token on state-changing requests"""
        if not current_app.config.get('WTF_CSRF_ENABLED', True):
            return None
        
        # Skip if method not in protected methods
        if request.method not in current_app.config.get('WTF_CSRF_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE']):
            return None
        
        # Skip if view is exempt
        if request.endpoint in self._exempt_views:
            return None
        
        # Skip if blueprint is exempt
        if request.blueprint in self._exempt_blueprints:
            return None
        
        # Check for API requests (JSON) - use header
        if request.is_json:
            token = request.headers.get(current_app.config.get('WTF_CSRF_HEADER_NAME', 'X-CSRFToken'))
        else:
            # Form submission - check form data
            token = request.form.get(current_app.config.get('WTF_CSRF_FIELD_NAME', 'csrf_token'))
            
            # Also check headers as fallback
            if not token:
                token = request.headers.get(current_app.config.get('WTF_CSRF_HEADER_NAME', 'X-CSRFToken'))
        
        if not self.validate_csrf_token(token):
            return jsonify({
                'success': False,
                'message': 'CSRF token missing or invalid',
                'error_code': 'CSRF_TOKEN_INVALID'
            }), 400
        
        return None
    
    def exempt(self, view):
        """Decorator to exempt a view from CSRF protection"""
        self._exempt_views.add(view.__name__)
        return view
    
    def exempt_blueprint(self, blueprint):
        """Exempt entire blueprint from CSRF protection"""
        self._exempt_blueprints.add(blueprint.name)
        return blueprint


# Initialize CSRF protection
csrf = CSRFProtect()


def csrf_exempt(view):
    """Decorator to exempt a view from CSRF protection"""
    csrf.exempt(view)
    return view


def csrf_protect(view):
    """Decorator to explicitly enable CSRF protection for a view"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        from flask import current_app
        # Temporarily enable CSRF for this view
        old_enabled = current_app.config.get('WTF_CSRF_ENABLED', True)
        current_app.config['WTF_CSRF_ENABLED'] = True
        try:
            return view(*args, **kwargs)
        finally:
            current_app.config['WTF_CSRF_ENABLED'] = old_enabled
    return view


# Helper functions for templates
def csrf_token():
    """Get CSRF token for templates"""
    return csrf.generate_csrf_token()


def csrf_input():
    """Get CSRF input field for templates"""
    return csrf.csrf_input()