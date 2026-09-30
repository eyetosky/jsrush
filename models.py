from flask_login import UserMixin

from datetime import datetime, timedelta, date

import bcrypt

import pyotp

import secrets

from itsdangerous import URLSafeTimedSerializer

import re

from flask import current_app



from extensions import db



class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(128), nullable=False)

    balance = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    last_login = db.Column(db.DateTime)

    is_admin = db.Column(db.Boolean, default=False)

    is_active = db.Column(db.Boolean, default=True)



    # Email verification

    email_verified = db.Column(db.Boolean, default=False)

    email_verification_token = db.Column(db.String(100))

    email_verification_sent_at = db.Column(db.DateTime)



    # 2FA

    two_fa_enabled = db.Column(db.Boolean, default=False)

    two_fa_secret = db.Column(db.String(32))



    # Age Verification

    date_of_birth = db.Column(db.Date, nullable=False)

    age_verified = db.Column(db.Boolean, default=False)

    age_verification_method = db.Column(db.String(50))

    age_verified_at = db.Column(db.DateTime)

    age_verification_expires = db.Column(db.DateTime)

    age_verification_reference = db.Column(db.String(100))



    # KYC

    kyc_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected

    kyc_level = db.Column(db.String(20), default='basic')  # basic, verified, vip

    kyc_documents = db.Column(db.Text)  # JSON string of document paths

    kyc_submitted_at = db.Column(db.DateTime)

    kyc_verified_at = db.Column(db.DateTime)

    kyc_rejected_reason = db.Column(db.Text)



    # KYC Documents

    id_document_front = db.Column(db.String(255))

    id_document_back = db.Column(db.String(255))

    selfie_document = db.Column(db.String(255))

    proof_of_address = db.Column(db.String(255))



    # Responsible Gambling

    daily_deposit_limit = db.Column(db.Float, default=50000)

    daily_loss_limit = db.Column(db.Float, default=20000)

    session_timeout = db.Column(db.Integer, default=1800)  # seconds

    self_excluded = db.Column(db.Boolean, default=False)

    self_excluded_until = db.Column(db.DateTime)

    cool_off_until = db.Column(db.DateTime)



    # KYC Documents

    id_document_front = db.Column(db.String(255))

    id_document_back = db.Column(db.String(255))

    selfie_document = db.Column(db.String(255))

    proof_of_address = db.Column(db.String(255))



    # Bank Details for Withdrawals (encrypted)

    bank_name = db.Column(db.String(100))

    bank_code = db.Column(db.String(10))

    account_number = db.Column(db.String(20))

    account_name = db.Column(db.String(100))

    bvn = db.Column(db.String(11))

    nin = db.Column(db.String(11))



    # Phone verification

    phone_number = db.Column(db.String(20), unique=True, nullable=False)

    phone_verified = db.Column(db.Boolean, default=False)

    phone_verification_token = db.Column(db.String(100))

    phone_verification_sent_at = db.Column(db.DateTime)

    phone_verified_at = db.Column(db.DateTime)

    # Whish Money Wallet
    whish_phone = db.Column(db.String(20))

    # Security Questions

    security_question = db.Column(db.String(200), nullable=True)

    security_answer_hash = db.Column(db.String(128), nullable=True)

    # Registration tracking

    registration_ip = db.Column(db.String(45), nullable=True)

    # Google OAuth

    google_id = db.Column(db.String(100), unique=True, nullable=True)

    google_email = db.Column(db.String(120), nullable=True)



    # Profile setup completed flag

    profile_completed = db.Column(db.Boolean, default=False)






    # Transaction limits

    daily_deposit_limit = db.Column(db.Float, default=50000)

    daily_loss_limit = db.Column(db.Float, default=20000)

    daily_withdrawal_limit = db.Column(db.Float, default=200000)

    max_single_bet = db.Column(db.Float, default=100000)



    # Security

    failed_login_attempts = db.Column(db.Integer, default=0)

    locked_until = db.Column(db.DateTime)

    last_password_change = db.Column(db.DateTime)

    api_key = db.Column(db.String(64))

    # Trusted Devices
    trusted_devices = db.Column(db.Text)  # JSON list of device fingerprints

    # Login notifications
    last_login_ip = db.Column(db.String(45))
    last_login_user_agent = db.Column(db.Text)
    last_login_at = db.Column(db.DateTime)


    # Encryption

    encrypted_fields = db.Column(db.Text)  # JSON list of encrypted field names



    # Notifications

    email_notifications = db.Column(db.Boolean, default=True)

    sms_notifications = db.Column(db.Boolean, default=True)

    marketing_emails = db.Column(db.Boolean, default=False)



    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    kyc_documents_rel = db.relationship('KYCDocument', backref='user', lazy=True, foreign_keys='KYCDocument.user_id')

    game_sessions = db.relationship('GameSession', backref='user', lazy=True)



    def set_password(self, password):

        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

        self.last_password_change = datetime.utcnow()



    def check_password(self, password):
        from flask import current_app
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        lockout_duration = current_app.config.get('LOGIN_LOCKOUT_DURATION', 900)
        
        if self.locked_until and self.locked_until > datetime.utcnow():
            return False

        if bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8')):
            self.failed_login_attempts = 0
            self.locked_until = None
            return True
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= max_attempts:
                self.locked_until = datetime.utcnow() + timedelta(seconds=lockout_duration)
            return False

    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True, int((self.locked_until - datetime.utcnow()).total_seconds())
        return False, 0

    def get_trusted_devices(self):
        """Get list of trusted device fingerprints"""
        if not self.trusted_devices:
            return []
        try:
            import json
            return json.loads(self.trusted_devices)
        except:
            return []

    def add_trusted_device(self, device_fingerprint):
        """Add a device to trusted devices"""
        devices = self.get_trusted_devices()
        if device_fingerprint not in devices:
            devices.append(device_fingerprint)
            import json
            self.trusted_devices = json.dumps(devices)

    def is_trusted_device(self, device_fingerprint):
        """Check if device is trusted"""
        return device_fingerprint in self.get_trusted_devices()

    def record_login(self, ip_address, user_agent):
        """Record successful login details"""
        self.last_login_ip = ip_address
        self.last_login_user_agent = user_agent
        self.last_login_at = datetime.utcnow()
        self.last_login = datetime.utcnow()

    def send_login_notification(self, ip_address, user_agent, location=None):
        """Send login notification email"""
        from flask import current_app
        if not current_app.config.get('LOGIN_NOTIFICATION_EMAIL', True):
            return
        if not self.email_notifications:
            return
        try:
            from extensions import mail
            from flask_mail import Message
            from flask import url_for
            
            # Extract device info from user agent
            device_info = "Unknown device"
            if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
                device_info = "Mobile device"
            elif "Windows" in user_agent:
                device_info = "Windows computer"
            elif "Macintosh" in user_agent or "Mac OS" in user_agent:
                device_info = "Mac computer"
            elif "Linux" in user_agent:
                device_info = "Linux computer"
            
            msg = Message(
                "New Login to Your JS Rush Account",
                recipients=[self.email]
            )
            msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #1a1a2e; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                        <h1 style="color: #ffd700; margin: 0;">JS<span style="color: #ff6b00;">RUSH</span></h1>
                    </div>
                    <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">
                        <h2 style="color: #1a1a2e;">New Login Detected</h2>
                        <p>Hello {self.username},</p>
                        <p>A new login was detected on your account:</p>
                        <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0;">
                            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                            <p><strong>Device:</strong> {device_info}</p>
                            <p><strong>IP Address:</strong> {ip_address}</p>
                            {f'<p><strong>Location:</strong> {location}</p>' if location else ''}
                        </div>
                        <p>If this was you, no action is needed. If you don't recognize this login, please:</p>
                        <ul>
                            <li>Change your password immediately</li>
                            <li>Enable 2FA if not already enabled</li>
                            <li>Contact support</li>
                        </ul>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{url_for('auth.change_password', _external=True)}" 
                               style="background: linear-gradient(135deg, #ff6b00, #ffd700); color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                                Change Password
                            </a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send login notification: {e}")

    @staticmethod
    def generate_device_fingerprint(user_agent, ip):
        """Generate a simple device fingerprint"""
        import hashlib
        data = f"{user_agent}|{ip}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]






    def set_security_answer(self, answer):

        """Hash and store security answer"""

        # Normalize: lowercase, strip whitespace
        normalized = answer.strip().lower()
        self.security_answer_hash = bcrypt.hashpw(
            normalized.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        db.session.commit()



    def check_security_answer(self, answer):

        """Verify security answer"""

        if not self.security_answer_hash:
            return False
        normalized = answer.strip().lower()
        return bcrypt.checkpw(
            normalized.encode('utf-8'),
            self.security_answer_hash.encode('utf-8')
        )



    def generate_email_verification_token(self):

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        self.email_verification_token = s.dumps(self.email, salt='email-verification')

        self.email_verification_sent_at = datetime.utcnow()

        db.session.commit()

        return self.email_verification_token

    @staticmethod

    def verify_email_verification_token(token, max_age=86400):
        try:
            s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = s.loads(token, salt="email-verification", max_age=max_age)
            return User.query.filter_by(email=email).first()
        except Exception as e:
            current_app.logger.error(f"Email verification token error: {e}")
            return None



    def generate_password_reset_token(self):

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        return s.dumps(self.email, salt='password-reset')

    @staticmethod

    def verify_password_reset_token(token, max_age=3600):

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:

            email = s.loads(token, salt='password-reset', max_age=max_age)

            return User.query.filter_by(email=email).first()
        except:

            return None



    def generate_2fa_secret(self):

        self.two_fa_secret = pyotp.random_base32()

        return self.two_fa_secret



    def get_2fa_qr_code(self):

        if not self.two_fa_secret:

            return None

        totp = pyotp.TOTP(self.two_fa_secret)

        uri = totp.provisioning_uri(self.email, issuer_name="JS Rush")

        import qrcode

        from io import BytesIO

        import base64

        qr = qrcode.make(uri)

        buffered = BytesIO()

        qr.save(buffered, format="PNG")

        return base64.b64encode(buffered.getvalue()).decode()



    def verify_2fa(self, code):

        if not self.two_fa_secret:

            return False

        totp = pyotp.TOTP(self.two_fa_secret)

        return totp.verify(code, valid_window=1)



    def generate_password_reset_token(self):

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        return s.dumps(self.email, salt='password-reset')

    @staticmethod

    def verify_password_reset_token(token, max_age=3600):

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:

            email = s.loads(token, salt='password-reset', max_age=max_age)

            return User.query.filter_by(email=email).first()
        except:

            return None



    def generate_api_key(self):

        self.api_key = secrets.token_urlsafe(32)

        return self.api_key



    def can_deposit(self, amount):

        if self.self_excluded and (not self.self_excluded_until or self.self_excluded_until > datetime.utcnow()):

            return False, "Account self-excluded"

        if self.cool_off_until and self.cool_off_until > datetime.utcnow():

            return False, "Account in cool-off period"

        if not self.is_active:

            return False, "Account deactivated"

        return True, None



    def can_withdraw(self, amount):

        if self.self_excluded:

            return False, "Account self-excluded"

        if not self.is_active:

            return False, "Account deactivated"

        if self.kyc_level == 'basic' and amount > 50000:

            return False, "KYC required for withdrawals above ₦50,000"

        return True, None



    def check_daily_deposit_limit(self, amount):

        from sqlalchemy import func

        today = datetime.utcnow().date()

        today_total = db.session.query(func.sum(Transaction.amount)).filter(

            Transaction.user_id == self.id,

            Transaction.type == 'deposit',

            func.date(Transaction.timestamp) == datetime.utcnow().date(),

            Transaction.amount > 0

        ).scalar() or 0

        return (today_total or 0) + amount <= self.daily_deposit_limit



    def check_daily_withdrawal_limit(self, amount):

        from sqlalchemy import func

        today_total = db.session.query(func.sum(Transaction.amount)).filter(

            Transaction.user_id == self.id,

            Transaction.type == 'withdraw',

            func.date(Transaction.timestamp) == datetime.utcnow().date(),

            Transaction.amount < 0

        ).scalar() or 0

        return abs(today_total or 0) + amount <= self.daily_withdrawal_limit



    def check_daily_loss_limit(self, amount):

        from sqlalchemy import func

        today_loss = db.session.query(func.sum(Transaction.amount)).filter(

            Transaction.user_id == self.id,

            Transaction.type == 'game',

            func.date(Transaction.timestamp) == datetime.utcnow().date(),

            Transaction.amount < 0

        ).scalar() or 0

        return abs(today_loss or 0) + amount <= self.daily_loss_limit



    def can_access_gambling(self) -> tuple:

        """Check if user can access gambling features"""

        if not self.date_of_birth:

            return False, "Date of birth required"



        if not self.email_verified:

            return False, "Email verification required"



        if not self.phone_verified:

            return False, "Phone number verification required"



        if not self.age_verified:

            return False, "Age verification required"



        if self.self_excluded:

            return False, "Account self-excluded"



        if not self.is_active:

            return False, "Account deactivated"



        from age_verification import AgeVerifier

        verifier = AgeVerifier()

        if not verifier.is_adult(self.date_of_birth):

            return False, f"Must be {AgeVerifier.LEGAL_GAMBLING_AGE}+ to gamble"



        return True, "OK"





    def verify_age(self, date_of_birth=None):

        """Verify user's age"""

        from age_verification import AgeVerifier

        verifier = AgeVerifier()

        dob = date_of_birth or self.date_of_birth

        if not dob:

            return False, "Date of birth required"



        result = verifier.verify_self_declared(dob)

        if result.verified:

            self.date_of_birth = dob

            self.age_verified = True

            self.age_verification_method = result.method.value

            self.age_verified_at = result.verified_at

            self.age_verification_expires = result.expires_at

            self.age_verification_reference = result.reference_id

            db.session.commit()

        return result.verified, result.message



    def submit_bvn_verification(self, bvn: str, dob: date):

        """Submit BVN for verification"""

        from age_verification import AgeVerifier

        verifier = AgeVerifier()

        result = verifier.verify_bvn(bvn, dob)

        if result.verified:

            self.bvn = bvn

            self.age_verified = True

            self.age_verification_method = result.method.value

            self.age_verified_at = result.verified_at

            self.age_verification_expires = result.expires_at

            self.age_verification_reference = result.reference_id

            db.session.commit()

        return result.verified, result.message



    def submit_nin_verification(self, nin: str, dob: date):

        """Submit NIN for verification"""

        from age_verification import AgeVerifier

        verifier = AgeVerifier()

        result = verifier.verify_nin(nin, dob)

        if result.verified:

            self.nin = nin

            self.age_verified = True

            self.age_verification_method = result.method.value

            self.age_verified_at = result.verified_at

            self.age_verification_expires = result.expires_at

            self.age_verification_reference = result.reference_id

            db.session.commit()

        return result.verified, result.message



    def submit_documents(self, documents: dict):

            """Submit documents for verification"""

            from age_verification import AgeVerifier

            verifier = AgeVerifier()

            result = verifier.verify_document('id_document', {

                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None

            })

            if result.verified:

                self.age_verified = True

                self.age_verification_method = result.method.value

                self.age_verified_at = result.verified_at

                self.age_verification_expires = result.expires_at

                self.age_verification_reference = result.reference_id

                db.session.commit()

            return result.verified, result.message



    def generate_phone_verification_token(self):

            """Generate phone verification token"""

            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

            self.phone_verification_token = s.dumps(self.phone_number, salt='phone-verification')

            self.phone_verification_sent_at = datetime.utcnow()

            db.session.commit()

            return self.phone_verification_token

    @staticmethod
    def verify_phone_verification_token(token, max_age=3600):

        """Verify phone verification token"""

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:

            phone_number = s.loads(token, salt='phone-verification', max_age=max_age)

            return User.query.filter_by(phone_number=phone_number).first()
        except:

            return None



    def verify_phone(self, token):

        """Verify phone number with token"""

        user = User.verify_phone_verification_token(token)

        if user:

            user.phone_verified = True

            user.phone_verified_at = datetime.utcnow()

            db.session.commit()

            return True, "Phone number verified successfully"

        return False, "Invalid or expired verification token"



    def send_phone_verification(self):
        """Send SMS verification code via Twilio (supports Lebanon)"""

        if not self.phone_number:

            return False, "No phone number on file"

        token = self.generate_phone_verification_token()

        # Send SMS via Twilio
        try:
            from flask import current_app
            from twilio.rest import Client

            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            from_number = current_app.config.get('TWILIO_PHONE_NUMBER')

            if account_sid and auth_token and from_number:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body=f"Your JS Rush verification code is: {token}. Valid for 1 hour.",
                    from_=from_number,
                    to=self.phone_number
                )
                return True, 'Verification code sent via SMS'
            else:
                current_app.logger.warning('Twilio credentials not configured')
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f'SMS send error: {e}')

        # Fallback: log token (development only)
        print(f"Phone verification token for {self.phone_number}: {self.phone_verification_token}")

        return True, "Verification code sent (check console in dev)"



    def can_access_gambling(self) -> tuple:

        """Check if user can access gambling features"""

        if not self.date_of_birth:

            return False, "Date of birth required"



        if not self.email_verified:

            return False, "Email verification required"



        if not self.phone_verified:

            return False, "Phone number verification required"



        if not self.age_verified:

            return False, "Age verification required"



        if self.self_excluded:

            return False, "Account self-excluded"



        if not self.is_active:

            return False, "Account deactivated"



        from age_verification import AgeVerifier

        verifier = AgeVerifier()

        if not verifier.is_adult(self.date_of_birth):

            return False, f"Must be {AgeVerifier.LEGAL_GAMBLING_AGE}+ to gamble"



        return True, "OK"



class Transaction(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    amount = db.Column(db.Float, nullable=False)

    type = db.Column(db.String(20), nullable=False)  # deposit, withdraw, game, admin

    description = db.Column(db.String(200))

    reference = db.Column(db.String(100))

    status = db.Column(db.String(20), default='completed')  # pending, completed, failed

    gateway = db.Column(db.String(50))  # whish

    gateway_reference = db.Column(db.String(100))

    gateway_response = db.Column(db.Text)  # JSON

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    processed_at = db.Column(db.DateTime)



    # For audit

    ip_address = db.Column(db.String(45))

    user_agent = db.Column(db.Text)

    tx_metadata = db.Column(db.Text)  # JSON



    # Encryption

    encrypted_data = db.Column(db.Text)  # Encrypted sensitive transaction data





class KYCDocument(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    document_type = db.Column(db.String(50))  # id_front, id_back, selfie, proof_address

    file_path = db.Column(db.String(255))

    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewed_at = db.Column(db.DateTime)

    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    rejection_reason = db.Column(db.Text)





class GameSession(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    game_type = db.Column(db.String(50))

    bet_amount = db.Column(db.Float)

    win_amount = db.Column(db.Float)

    result = db.Column(db.String(50))

    game_data = db.Column(db.Text)  # JSON - full game state for replay

    started_at = db.Column(db.DateTime, default=datetime.utcnow)

    ended_at = db.Column(db.DateTime)

    duration = db.Column(db.Integer)  # seconds

    client_ip = db.Column(db.String(45))

    user_agent = db.Column(db.Text)

    server_seed = db.Column(db.String(64))  # For provably fair

    client_seed = db.Column(db.String(64))

    nonce = db.Column(db.Integer)





class AuditLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    action = db.Column(db.String(100))

    details = db.Column(db.Text)

    ip_address = db.Column(db.String(45))

    user_agent = db.Column(db.Text)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)





class ResponsibleGamblingLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    action = db.Column(db.String(50))  # deposit_limit_set, loss_limit_set, self_exclude, cool_off, timeout

    old_value = db.Column(db.Float)

    new_value = db.Column(db.Float)

    duration = db.Column(db.Integer)  # days for self-exclusion

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    ip_address = db.Column(db.String(45))