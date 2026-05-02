from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.throttling import SimpleRateThrottle

from .serializers import SendOTPSerializer, VerifyOTPSerializer, UserSerializer
from .services.otp_service import OTPService

User = get_user_model()

class OTPRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        phone = request.data.get('phone')
        if not phone:
            return None
        return self.cache_format % {
            'scope': 'otp_requests',
            'ident': phone
        }

    def get_rate(self):
        return 'dummy' # Bypass settings lookup

    def parse_rate(self, rate):
        return (3, 600)  # 3 requests per 600 seconds (10 minutes)

class SendOTPView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data[0] if isinstance(request.data, list) and request.data else request.data
        serializer = SendOTPSerializer(data=data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            try:
                otp_record, raw_otp = OTPService.send_otp(phone)
                # Including `otp` in response for testing/development
                return Response({"message": "OTP sent successfully", "otp": raw_otp}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print(f"--- Frontend Data Received ---")
        data = request.data[0] if isinstance(request.data, list) and request.data else request.data
        print(f"Raw Request Data: {request.data}")
        print(f"Data after processing: {data}")
        print(f"Role in Request Data: {request.data.get('role')}")
        print(f"------------------------------")
        
        serializer = VerifyOTPSerializer(data=data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']
            role = serializer.validated_data.get('role', 'parent')
            print(f"Role after serializer validation: {role}")

            try:
                OTPService.verify_otp(phone, otp)
            except ValueError as e:
                print(f"OTP verification failed: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            if role == "parent":
                from academy.models import Student
                from django.db.models import Q
                
                # Handle cases where the teacher saved the phone number without +91 prefix
                raw_phone = phone.replace('+91', '') if phone.startswith('+91') else phone
                student = Student.objects.filter(
                    Q(parent_phone=phone) | Q(parent_phone=raw_phone)
                ).first()

                if not student:
                    return Response({
                        "error": "Parent not registered. Please contact teacher."
                    }, status=400)

                # Fetch or create the parent User since they passed OTP and the student exists
                user, created = User.objects.get_or_create(
                    phone=phone,
                    defaults={'role': 'parent'}
                )
                
                # Ensure the student is linked to this user profile
                if not student.parent:
                    student.parent = user
                    student.save()
                
                # Generate Tokens
                refresh = RefreshToken.for_user(user)
                user_data = UserSerializer(user).data

                return Response({
                    "message": "Login successful",
                    "student_id": student.id,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": user_data
                }, status=status.HTTP_200_OK)

            elif role == "teacher":
                # OTP is valid for teacher, allow login normally
                user, created = User.objects.get_or_create(phone=phone, defaults={'role': 'teacher'})
                
                # Generate Tokens
                refresh = RefreshToken.for_user(user)
                user_data = UserSerializer(user).data

                return Response({
                    "message": "Login successful",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": user_data
                }, status=status.HTTP_200_OK)

        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data[0] if isinstance(request.data, list) and request.data else request.data
            refresh_token = data.get("refresh") if isinstance(data, dict) else None
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token or already logged out."}, status=status.HTTP_400_BAD_REQUEST)
