import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(app):
    """Configure application logging"""
    
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
    ))
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
    ))
    
    # Security audit log handler
    audit_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'audit.log'),
        maxBytes=50*1024*1024,  # 50MB
        backupCount=30
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(logging.Formatter(
        '%(asctime)s AUDIT %(message)s'
    ))
    audit_logger = logging.getLogger('audit')
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    
    # Game events logger
    game_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'games.log'),
        maxBytes=20*1024*1024,
        backupCount=10
    )
    game_handler.setLevel(logging.INFO)
    game_handler.setFormatter(logging.Formatter(
        '%(asctime)s GAME %(message)s'
    ))
    game_logger = logging.getLogger('games')
    game_logger.addHandler(game_handler)
    game_logger.setLevel(logging.INFO)
    game_logger.propagate = False
    
    # Payment logger
    payment_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'payments.log'),
        maxBytes=20*1024*1024,
        backupCount=10
    )
    payment_handler.setLevel(logging.INFO)
    payment_handler.setFormatter(logging.Formatter(
        '%(asctime)s PAYMENT %(message)s'
    ))
    payment_logger = logging.getLogger('payments')
    payment_logger.addHandler(payment_handler)
    payment_logger.setLevel(logging.INFO)
    payment_logger.propagate = False
    
    # Add handlers to Flask app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Suppress noisy loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return {
        'audit': audit_logger,
        'games': game_logger,
        'payments': payment_logger
    }


def get_audit_logger():
    """Get audit logger instance"""
    return logging.getLogger('audit')


def get_game_logger():
    """Get game events logger"""
    return logging.getLogger('games')


def get_payment_logger():
    """Get payments logger"""
    return logging.getLogger('payments')


class AuditLogger:
    """Structured audit logger for compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
    
    def log(self, user_id, admin_id, action, details, ip_address=None, user_agent=None):
        """Log an audit event"""
        self.logger.info(
            'user_id=%s admin_id=%s action=%s details=%s ip=%s ua=%s',
            user_id, admin_id, action, details, ip_address, user_agent
        )
    
    def log_deposit(self, user_id, amount, gateway, reference):
        self.log(None, None, 'deposit', {
            'amount': amount,
            'gateway': gateway,
            'reference': reference
        })
    
    def log_withdrawal(self, user_id, amount, gateway, reference):
        self.log(None, None, 'withdrawal', {
            'amount': amount,
            'gateway': gateway,
            'reference': reference
        })
    
    def log_game(self, user_id, game_type, bet, win, amount, details):
        self.log(None, None, 'game_played', {
            'game': game_type,
            'bet': bet,
            'win': win,
            'amount': amount,
            'details': details
        })
    
    def log_admin_action(self, admin_id, user_id, action, details):
        self.log(None, admin_id, action, details)
    
    def log_kyc(self, user_id, action, details):
        self.log(None, None, f'kyc_{action}', details)
    
    def log_security(self, user_id, event, details, ip_address=None):
        self.log(None, None, f'security_{event}', details, ip_address)