# Add to models.py - Age Verification and Encryption fields

# Add to User model:
# Age verification fields
# date_of_birth = db.Column(db.Date)
# age_verified = db.Column(db.Boolean, default=False)
# age_verification_method = db.Column(db.String(50))
# age_verified_at = db.Column(db.DateTime)
# age_verification_expires = db.Column(db.DateTime)

# Encryption fields
# encrypted_fields = db.Column(db.Text)  # JSON list of encrypted field names

# For Transaction model:
# encrypted_data = db.Column(db.Text)  # Encrypted sensitive transaction data