from rest_framework import serializers
from .models import CustomUser
from .utils.helpers import validate_phone_number

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone', 'full_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)
    role = serializers.ChoiceField(choices=['teacher', 'parent'], default='parent', required=False)

    def validate_phone(self, value):
        return validate_phone_number(str(value).strip())

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)
    otp = serializers.CharField(max_length=10)  # Allow a bit more so we can strip it
    role = serializers.ChoiceField(choices=['teacher', 'parent'], default='parent', required=False)

    def validate_phone(self, value):
        return validate_phone_number(str(value).strip())

    def validate_otp(self, value):
        return str(value).strip()
