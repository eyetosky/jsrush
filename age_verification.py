"""
Age Verification Module
Handles age verification for gambling compliance (18+ in Nigeria)
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import json


class VerificationMethod(Enum):
    """Age verification methods"""
    SELF_DECLARED = "self_declared"
    DOCUMENT_VERIFICATION = "document_verification"
    BVN_VERIFICATION = "bvn_verification"  # Bank Verification Number (Nigeria)
    NIN_VERIFICATION = "nin_verification"  # National Identity Number (Nigeria)
    THIRD_PARTY_API = "third_party_api"


class VerificationStatus(Enum):
    """Verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    MANUAL_REVIEW = "manual_review"


@dataclass
class AgeVerificationResult:
    """Result of age verification"""
    verified: bool
    age: Optional[int] = None
    method: Optional[VerificationMethod] = None
    status: VerificationStatus = VerificationStatus.PENDING
    message: str = ""
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reference_id: Optional[str] = None


class AgeVerifier:
    """Age verification service for gambling compliance"""
    
    # Legal gambling age in Nigeria
    LEGAL_GAMBLING_AGE = 18
    
    # Verification expiry (1 year)
    VERIFICATION_EXPIRY_DAYS = 365
    
    def __init__(self, api_keys: dict = None):
        self.api_keys = api_keys or {}
        self.third_party_providers = {}
    
    def calculate_age(self, date_of_birth: date) -> int:
        """Calculate age from date of birth"""
        today = date.today()
        age = today.year - date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        return age
    
    def is_adult(self, date_of_birth: date) -> bool:
        """Check if person is of legal gambling age"""
        return self.calculate_age(date_of_birth) >= self.LEGAL_GAMBLING_AGE
    
    def verify_self_declared(self, date_of_birth: date, user_id: str = None) -> AgeVerificationResult:
        """Verify age from self-declared date of birth"""
        age = self.calculate_age(date_of_birth)
        is_adult = age >= self.LEGAL_GAMBLING_AGE
        
        if is_adult:
            return AgeVerificationResult(
                verified=True,
                age=age,
                method=VerificationMethod.SELF_DECLARED,
                status=VerificationStatus.VERIFIED,
                message=f"Age verified: {age} years old",
                verified_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.VERIFICATION_EXPIRY_DAYS)
            )
        else:
            return AgeVerificationResult(
                verified=False,
                age=age,
                method=VerificationMethod.SELF_DECLARED,
                status=VerificationStatus.REJECTED,
                message=f"Underage: {age} years old. Minimum age is {self.LEGAL_GAMBLING_AGE}."
            )
    
    def verify_bvn(self, bvn: str, date_of_birth: date, user_id: str = None) -> AgeVerificationResult:
        """Verify age using Bank Verification Number (Nigeria)"""
        # In production, integrate with NIBSS or approved BVN verification service
        # This is a placeholder implementation
        
        # Validate BVN format (11 digits)
        if not re.match(r'^\d{11}$', bvn):
            return AgeVerificationResult(
                verified=False,
                method=VerificationMethod.BVN_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message="Invalid BVN format. Must be 11 digits."
            )
        
        # In production, call NIBSS/approved BVN verification API
        # Example integration:
        """
        headers = {'Authorization': f'Bearer {self.api_keys.get("bvn_api_key")}'}
        response = requests.post(
            'https://api.nibss.gov.ng/bvn/verify',
            json={'bvn': bvn, 'date_of_birth': date_of_birth.isoformat()},
            headers=headers
        )
        """
        
        # For now, calculate age from provided DOB
        age = self.calculate_age(date_of_birth)
        is_adult = age >= self.LEGAL_GAMBLING_AGE
        
        if is_adult:
            return AgeVerificationResult(
                verified=True,
                age=age,
                method=VerificationMethod.BVN_VERIFICATION,
                status=VerificationStatus.VERIFIED,
                message=f"BVN verification successful. Age: {age}",
                verified_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.VERIFICATION_EXPIRY_DAYS),
                reference_id=f"BVN_{bvn[-4:]}"
            )
        else:
            return AgeVerificationResult(
                verified=False,
                age=age,
                method=VerificationMethod.BVN_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message=f"Underage: {age} years old."
            )
    
    def verify_nin(self, nin: str, date_of_birth: date, user_id: str = None) -> AgeVerificationResult:
        """Verify age using National Identity Number (Nigeria)"""
        # Validate NIN format (11 digits)
        if not re.match(r'^\d{11}$', nin):
            return AgeVerificationResult(
                verified=False,
                method=VerificationMethod.NIN_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message="Invalid NIN format. Must be 11 digits."
            )
        
        # In production, integrate with NIMC API
        age = self.calculate_age(date_of_birth)
        is_adult = age >= self.LEGAL_GAMBLING_AGE
        
        if is_adult:
            return AgeVerificationResult(
                verified=True,
                age=age,
                method=VerificationMethod.NIN_VERIFICATION,
                status=VerificationStatus.VERIFIED,
                message=f"NIN verification successful. Age: {age}",
                verified_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.VERIFICATION_EXPIRY_DAYS),
                reference_id=f"NIN_{nin[-4:]}"
            )
        else:
            return AgeVerificationResult(
                verified=False,
                age=age,
                method=VerificationMethod.NIN_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message=f"Underage: {age} years old."
            )
    
    def verify_document(self, document_type: str, document_data: dict) -> AgeVerificationResult:
        """Verify age from uploaded document (ID, passport, etc.)"""
        # In production, use OCR/document verification service
        # This extracts DOB from document and verifies
        
        # Placeholder implementation
        date_of_birth = document_data.get('date_of_birth')
        if not date_of_birth:
            return AgeVerificationResult(
                verified=False,
                method=VerificationMethod.DOCUMENT_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message="Date of birth not found in document"
            )
        
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.fromisoformat(date_of_birth).date()
        
        age = self.calculate_age(date_of_birth)
        is_adult = age >= self.LEGAL_GAMBLING_AGE
        
        if is_adult:
            return AgeVerificationResult(
                verified=True,
                age=age,
                method=VerificationMethod.DOCUMENT_VERIFICATION,
                status=VerificationStatus.VERIFIED,
                message=f"Document verified. Age: {age}",
                verified_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.VERIFICATION_EXPIRY_DAYS)
            )
        else:
            return AgeVerificationResult(
                verified=False,
                age=age,
                method=VerificationMethod.DOCUMENT_VERIFICATION,
                status=VerificationStatus.REJECTED,
                message=f"Underage: {age} years old."
            )
    
    def verify_third_party(self, provider: str, user_data: dict) -> AgeVerificationResult:
        """Verify age using third-party age verification service"""
        # Integrate with services like:
        # - Veriff, Onfido, Jumio, Shufti Pro
        # - AgeChecked, AgeID
        
        provider = provider.lower()
        
        if provider == 'veriff':
            return self._verify_veriff(user_data)
        elif provider == 'onfido':
            return self._verify_onfido(user_data)
        elif provider == 'jumio':
            return self._verify_jumio(user_data)
        else:
            return AgeVerificationResult(
                verified=False,
                method=VerificationMethod.THIRD_PARTY_API,
                status=VerificationStatus.REJECTED,
                message=f"Unknown provider: {provider}"
            )
    
    def _verify_veriff(self, user_data: dict) -> AgeVerificationResult:
        """Verify using Veriff API"""
        # Implementation would call Veriff API
        # Placeholder
        return AgeVerificationResult(
            verified=False,
            method=VerificationMethod.THIRD_PARTY_API,
            status=VerificationStatus.PENDING,
            message="Veriff integration not implemented"
        )
    
    def _verify_onfido(self, user_data: dict) -> AgeVerificationResult:
        """Verify using Onfido API"""
        # Placeholder
        return AgeVerificationResult(
            verified=False,
            method=VerificationMethod.THIRD_PARTY_API,
            status=VerificationStatus.PENDING,
            message="Onfido integration not implemented"
        )
    
    def _verify_jumio(self, user_data: dict) -> AgeVerificationResult:
        """Verify using Jumio API"""
        # Placeholder
        return AgeVerificationResult(
            verified=False,
            method=VerificationMethod.THIRD_PARTY_API,
            status=VerificationStatus.PENDING,
            message="Jumio integration not implemented"
        )
    
    def check_verification_expiry(self, verified_at: datetime, method: VerificationMethod) -> bool:
        """Check if verification has expired"""
        if not verified_at:
            return True  # Expired
        
        expiry_days = self.VERIFICATION_EXPIRY_DAYS
        if method == VerificationMethod.SELF_DECLARED:
            expiry_days = 30  # Self-declared expires faster
        
        expiry_date = verified_at + timedelta(days=expiry_days)
        return datetime.utcnow() > expiry_date
    
    def get_verification_requirements(self, amount: float = None) -> dict:
        """Get verification requirements based on amount/activity"""
        requirements = {
            'basic': {
                'min_age': self.LEGAL_GAMBLING_AGE,
                'methods': [VerificationMethod.SELF_DECLARED],
                'max_deposit': 50000,
                'max_withdrawal': 50000
            },
            'verified': {
                'min_age': self.LEGAL_GAMBLING_AGE,
                'methods': [
                    VerificationMethod.BVN_VERIFICATION,
                    VerificationMethod.NIN_VERIFICATION,
                    VerificationMethod.DOCUMENT_VERIFICATION,
                    VerificationMethod.THIRD_PARTY_API
                ],
                'max_deposit': 1000000,
                'max_withdrawal': 500000
            }
        }
        
        if amount and amount > 50000:
            return requirements['verified']
        return requirements['basic']


# Integration with User model
class UserAgeVerificationMixin:
    """Mixin for User model to add age verification methods"""
    
    def verify_age(self, date_of_birth: date) -> AgeVerificationResult:
        """Verify user's age"""
        verifier = AgeVerifier()
        return verifier.verify_self_declared(date_of_birth)
    
    def submit_bvn_verification(self, bvn: str, dob: date) -> AgeVerificationResult:
        """Submit BVN for verification"""
        verifier = AgeVerifier()
        return verifier.verify_bvn(bvn, self.date_of_birth)
    
    def submit_nin_verification(self, nin: str, dob: date) -> AgeVerificationResult:
        """Submit NIN for verification"""
        verifier = AgeVerifier()
        return verifier.verify_nin(nin, self.date_of_birth)
    
    def submit_documents(self, documents: dict) -> AgeVerificationResult:
        """Submit documents for verification"""
        verifier = AgeVerifier()
        return verifier.verify_document('id_document', {
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None
        })
    
    def can_access_gambling(self) -> Tuple[bool, str]:
        """Check if user can access gambling features"""
        if not self.date_of_birth:
            return False, "Date of birth required"
        
        if not self.email_verified:
            return False, "Email verification required"
        
        if self.self_excluded:
            return False, "Account self-excluded"
        
        verifier = AgeVerifier()
        if not verifier.is_adult(self.date_of_birth):
            return False, f"Must be {AgeVerifier.LEGAL_GAMBLING_AGE}+ to gamble"
        
        return True, "OK"