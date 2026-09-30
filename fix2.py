with open('models.py', 'rb') as f:
    content = f.read()

# Fix verify_phone_verification_token method
old = b'    def verify_phone_verification_token(token, max_age=3600):\r\n\r\n        """Verify phone verification token"""\r\n\r\n        s = URLSafeTimedSerializer(current_app.config[\'SECRET_KEY\'])\r\n        try:\r\n            phone_number = s.loads(token, salt=\'phone-verification\', max_age=max_age)\r\n\r\n            return User.query.filter_by(phone_number=phone_number).first()\r\n        except:\r\n            return None'

new = b'    def verify_phone_verification_token(token, max_age=3600):\r\n        """Verify phone verification token"""\r\n        s = URLSafeTimedSerializer(current_app.config[\'SECRET_KEY\'])\r\n        try:\r\n            phone_number = s.loads(token, salt=\'phone-verification\', max_age=max_age)\r\n            return User.query.filter_by(phone_number=phone_number).first()\r\n        except:\r\n            return None'

content = content.replace(
    b'    def verify_phone_verification_token(token, max_age=3600):\r\n\r\n        """Verify phone verification token"""\r\n\r\n        s = URLSafeTimedSerializer(current_app.config[\'SECRET_KEY\'])\r\n        try:\r\n            phone_number = s.loads(token, salt=\'phone-verification\', max_age=max_age)\r\n\r\n            return User.query.filter_by(phone_number=phone_number).first()\r\n        except:\r\n            return None',
    b'    def verify_phone_verification_token(token, max_age=3600):\r\n        """Verify phone verification token"""\r\n        s = URLSafeTimedSerializer(current_app.config[\'SECRET_KEY\'])\r\n        try:\r\n            phone_number = s.loads(token, salt=\'phone-verification\', max_age=max_age)\r\n            return User.query.filter_by(phone_number=phone_number).first()\r\n        except:\r\n            return None'
)

with open('models.py', 'wb') as f:
    f.write(content)

print('Fixed!')