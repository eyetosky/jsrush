with open(r'C:\Users\ASUS ROG\Desktop\jean\gamble web\models.py', 'r') as f:
    content = f.read()

# Find the function and replace it
import re
pattern = r'(def verify_email_verification_token\(token, max_age=86400\):.*?return None)'
replacement = '''def verify_email_verification_token(token, max_age=86400):
        try:
            s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = s.loads(token, salt="email-verification", max_age=max_age)
            return User.query.filter_by(email=email).first()
        except Exception as e:
            current_app.logger.error(f"Email verification token error: {e}")
            return None'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
with open(r'C:\Users\ASUS ROG\Desktop\jean\gamble web\models.py', 'w') as f:
    f.write(new_content)
print('Done')