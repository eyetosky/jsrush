"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db

# Get config from environment
config_name = os.environ.get('FLASK_ENV', 'production')
from config import ProductionConfig, DevelopmentConfig

if os.environ.get('FLASK_ENV') == 'production':
    from config import ProductionConfig
    app = create_app('production')
else:
    from config import DevelopmentConfig
    app = create_app('development')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)