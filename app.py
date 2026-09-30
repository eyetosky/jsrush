from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from config import config, DevelopmentConfig, ProductionConfig
from extensions import db, login_manager, limiter, mail, migrate, init_extensions, redis_client
import random
from datetime import datetime
import os
from dotenv import load_dotenv
import secrets
import json

load_dotenv()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        from config import TestingConfig
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    init_extensions(app)
    
# Import models after extensions are initialized
    from models import User, Transaction

    # Template filters
    @app.template_filter('format_number')
    def format_number(value):
        """Format number with comma separators"""
        try:
            return f"{float(value):,.2f}".rstrip('0').rstrip('.') if '.' in f"{float(value):,.2f}" else f"{int(value):,}"
        except (ValueError, TypeError):
            return value
    
    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.whish.money https://whish.money https://cdn.ravenjs.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.whish.money https://whish.money https://lb.sandbox.whish.money;"
        return response
    
    # Create tables
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(is_admin=True).first():
            from datetime import date
            admin = User(
                username='admin', 
                email='admin@jsrush.com', 
                is_admin=True, 
                balance=999999,
                email_verified=True,
                kyc_status='verified',
                kyc_level='full',
                date_of_birth=date(1990, 1, 1),
                age_verified=True,
                phone_number='+96100000000',
                phone_verified=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
    
    # Register blueprints
    register_blueprints(app)
    register_error_handlers(app)
    
    return app


def register_blueprints(app):
    # Game blueprints
    from games.slots import slots_bp
    from games.blackjack import blackjack_bp
    from games.roulette import roulette_bp
    from games.dice import dice_bp
    from games.crash import crash_bp
    from games.mines import mines_bp
    from games.craps import craps_bp
    from games.videopoker import videopoker_bp
    from games.barakat import barakat_bp
    from games.bingo import bingo_bp
    from games.electronic import electronic_bp
    from games.craps import craps_bp
    
    # Core blueprints
    from auth.routes import auth_bp
    from user.routes import user_bp
    from user.responsible_routes import responsible_bp
    from admin.routes import admin_bp
    from payments.routes import deposit_bp
    from payments.kyc_routes import kyc_bp
    from payments.webhooks import webhook_bp
    from fairness_routes import fairness_bp
    
    app.register_blueprint(slots_bp)
    app.register_blueprint(blackjack_bp)
    app.register_blueprint(roulette_bp)
    app.register_blueprint(dice_bp)
    app.register_blueprint(crash_bp)
    app.register_blueprint(mines_bp)
    app.register_blueprint(craps_bp)
    app.register_blueprint(videopoker_bp)
    app.register_blueprint(barakat_bp)
    app.register_blueprint(bingo_bp)
    app.register_blueprint(electronic_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp)
    app.register_blueprint(responsible_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(deposit_bp)
    app.register_blueprint(kyc_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(fairness_bp)
    
    # Core routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'jsrush'})
    
    @app.route('/robots.txt')
    def robots():
        return 'User-agent: *\nDisallow: /admin\nDisallow: /api/'
    
    @app.route('/api/banks')
    def get_banks():
        """Get list of Nigerian banks for withdrawal"""
        banks = [
            {'code': '044', 'name': 'Access Bank'},
            {'code': '014', 'name': 'Afribank'},
            {'code': '023', 'name': 'Citibank'},
            {'code': '050', 'name': 'Ecobank'},
            {'code': '084', 'name': 'Enterprise Bank'},
            {'code': '070', 'name': 'Fidelity Bank'},
            {'code': '011', 'name': 'First Bank'},
            {'code': '214', 'name': 'First City Monument Bank'},
            {'code': '058', 'name': 'Guaranty Trust Bank'},
            {'code': '030', 'name': 'Heritage Bank'},
            {'code': '082', 'name': 'Keystone Bank'},
            {'code': '076', 'name': 'Polaris Bank'},
            {'code': '101', 'name': 'Providus Bank'},
            {'code': '221', 'name': 'Stanbic IBTC Bank'},
            {'code': '068', 'name': 'Standard Chartered Bank'},
            {'code': '232', 'name': 'Sterling Bank'},
            {'code': '100', 'name': 'Suntrust Bank'},
            {'code': '032', 'name': 'Union Bank'},
            {'code': '033', 'name': 'United Bank for Africa'},
            {'code': '215', 'name': 'Unity Bank'},
            {'code': '035', 'name': 'Wema Bank'},
            {'code': '057', 'name': 'Zenith Bank'},
            {'code': '090110', 'name': 'Opay'},
            {'code': '090111', 'name': 'PalmPay'},
            {'code': '090112', 'name': 'Kuda Bank'},
            {'code': '090113', 'name': 'Carbon'},
            {'code': '090114', 'name': 'FairMoney'},
        ]
        return jsonify({'success': True, 'banks': banks})
    
    @app.route('/api/banks/verify', methods=['POST'])
    def verify_bank_account():
        data = request.get_json()
        account_number = data.get('account_number')
        bank_code = data.get('bank_code')
        
        # In production, verify with Paystack/Flutterwave
        # For now, return mock data
        if len(account_number) == 10 and account_number.isdigit():
            return jsonify({
                'success': True,
                'account_name': f'TEST USER {account_number[-4:]}',
                'account_number': account_number,
                'bank_code': bank_code
            })
        return jsonify({'success': False, 'message': 'Invalid account number'}), 400


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'success': False, 'message': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'success': False, 'message': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Not found'}), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({'success': False, 'message': 'Rate limit exceeded. Please slow down.'}), 429
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=app.config.get('FLASK_DEBUG', False))