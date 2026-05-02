import random
import string
import requests
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
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
        Generate, store, and send the OTP using Fast2SMS API.
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

        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if not api_key:
            print(f"WARNING: FAST2SMS_API_KEY is not set. OTP {otp} for {phone} was NOT sent.")
            return otp_record, otp

        # Fast2SMS requires 10-digit numbers without the country code
        clean_phone = phone.replace('+91', '') if phone.startswith('+91') else phone

        # Fast2SMS OTP API call
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": f"Your KalviConnect verification code is: {otp}",
            "language": "english",
            "flash": 0,
            "numbers": clean_phone
        }
        headers = {
            'authorization': api_key,
            'Content-Type': "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            response_data = response.json()
            if response_data.get('return') == True:
                print(f"SMS successfully sent to {phone}")
            else:
                print(f"Fast2SMS API Error: {response_data.get('message')}")
        except Exception as e:
            print(f"Failed to send SMS to {phone}. Error: {str(e)}")

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
