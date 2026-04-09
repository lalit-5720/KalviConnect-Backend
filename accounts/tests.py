from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from accounts.models import OTPVerification
from accounts.services.otp_service import OTPService

User = get_user_model()

class OTPAuthTests(APITestCase):

    def setUp(self):
        self.phone = '+919876543210'
        self.send_otp_url = reverse('send-otp')
        self.verify_otp_url = reverse('verify-otp')
        
    def test_send_otp_success(self):
        data = {'phone': self.phone}
        response = self.client.post(self.send_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(OTPVerification.objects.count(), 1)
        
    def test_send_otp_invalid_phone(self):
        data = {'phone': '12345'}
        response = self.client.post(self.send_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_otp_success_teacher(self):
        OTPVerification.objects.all().delete()
        
        with patch.object(OTPService, 'generate_otp', return_value='123456'):
            self.client.post(self.send_otp_url, {'phone': self.phone, 'role': 'teacher'})
            
        data = {'phone': self.phone, 'otp': '123456', 'role': 'teacher'}
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(User.objects.filter(role='teacher').count(), 1)
        
    def test_verify_otp_parent_fails_if_no_student(self):
        OTPVerification.objects.all().delete()
        
        with patch.object(OTPService, 'generate_otp', return_value='123456'):
            self.client.post(self.send_otp_url, {'phone': self.phone, 'role': 'parent'})
            
        data = {'phone': self.phone, 'otp': '123456', 'role': 'parent'}
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(User.objects.count(), 0)
        
    def test_verify_otp_invalid_otp(self):
        with patch.object(OTPService, 'generate_otp', return_value='123456'):
            self.client.post(self.send_otp_url, {'phone': self.phone})
            
        data = {'phone': self.phone, 'otp': '000000'}
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_otp_defaults_to_parent_role(self):
        OTPVerification.objects.all().delete()
        with patch.object(OTPService, 'generate_otp', return_value='123456'):
            self.client.post(self.send_otp_url, {'phone': self.phone})

        data = {'phone': self.phone, 'otp': '123456'}
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_otp_expired(self):
        with patch.object(OTPService, 'generate_otp', return_value='123456'):
            self.client.post(self.send_otp_url, {'phone': self.phone})
            
        otp_record = OTPVerification.objects.latest('created_at')
        otp_record.expires_at = timezone.now() - timedelta(minutes=1)
        otp_record.save()
        
        data = {'phone': self.phone, 'otp': '123456'}
        response = self.client.post(self.verify_otp_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class RateLimitTests(APITestCase):

    def setUp(self):
        self.phone = '+919876543211'
        self.send_otp_url = reverse('send-otp')

    def test_rate_limiting(self):
        # Django REST framework throttle cache defaults to locmem during testing
        # We send 3 messages, 4th should be blocked by 3/10m throttle
        for _ in range(3):
            response = self.client.post(self.send_otp_url, {'phone': self.phone})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        response = self.client.post(self.send_otp_url, {'phone': self.phone})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
