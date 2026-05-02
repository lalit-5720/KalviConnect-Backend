from django.contrib import admin
from .models import CustomUser, OTPVerification

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'role', 'full_name', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('phone', 'full_name')

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp_code', 'is_used', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('phone',)
