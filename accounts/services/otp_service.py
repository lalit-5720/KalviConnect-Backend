import random
import string
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import OTPVerification

class OTPService:
    OTP_EXPIRY_MINUTES = 5

    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP."""
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def send_otp(cls, phone):
        """
        Generate, store, and 'send' the OTP. 
        In development, we print to the console.
        """
        otp = cls.generate_otp()
        hashed_otp = make_password(otp)
        expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
        
        # Save OTP to database
        otp_record = OTPVerification.objects.create(
            phone=phone,
            otp_code=hashed_otp,
            expires_at=expires_at
        )

        # Mock Sending OTP
        print(f"\n{'='*40}")
        print(f"MOCK SMS SERVICE")
        print(f"To: {phone}")
        print(f"Your KalviConnect OTP is: {otp}")
        print(f"It expires in {cls.OTP_EXPIRY_MINUTES} minutes.")
        print(f"{'='*40}\n")

        return otp_record, otp

    @classmethod
    def verify_otp(cls, phone, otp):
        """
        Verify the given OTP for the phone number.
        Returns True if valid, raises ValueError otherwise.
        """
        try:
            # Get the latest unused OTP request for this phone
            otp_record = OTPVerification.objects.filter(
                phone=phone, is_used=False
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            raise ValueError("No valid pending OTP request found for this number.")

        if timezone.now() > otp_record.expires_at:
            raise ValueError("OTP has expired.")
            
        if not check_password(otp, otp_record.otp_code):
            raise ValueError("Invalid OTP.")

        # Mark as used
        otp_record.is_used = True
        otp_record.save()
        return True
