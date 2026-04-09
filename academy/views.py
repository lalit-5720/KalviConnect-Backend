from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .models import Student, Mark, FeeRecord, Attendance, Announcement
from .serializers import (
    StudentSerializer, MarkSerializer, FeeRecordSerializer,
    AttendanceSerializer, BulkAttendanceSerializer, AnnouncementSerializer
)
from .permissions import IsTeacher

User = get_user_model()

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        user = request.user
        # Total Students
        total_students = Student.objects.filter(teacher=user).count()
        
        # Pending Fees
        pending_fees_aggregates = FeeRecord.objects.filter(
            student__teacher=user,
            status='pending'
        ).aggregate(
            total_amount_sum=Sum('total_amount'), 
            amount_paid_sum=Sum('amount_paid')
        )
        total_amount_sum = pending_fees_aggregates.get('total_amount_sum') or 0
        amount_paid_sum = pending_fees_aggregates.get('amount_paid_sum') or 0
        pending_fees = total_amount_sum - amount_paid_sum

        # Recent Announcements (e.g. from the last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_announcements = Announcement.objects.filter(
            created_at__gte=seven_days_ago
        ).count()

        return Response({
            "total_students": total_students,
            "pending_fees": float(pending_fees),
            "recent_announcements": recent_announcements
        }, status=status.HTTP_200_OK)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        queryset = Student.objects.filter(teacher=user)
        
        # Search & Filter by class/section
        search = self.request.query_params.get('search', None)
        class_name = self.request.query_params.get('class', None)
        section = self.request.query_params.get('section', None)

        if search:
            queryset = queryset.filter(full_name__icontains=search)
        if class_name:
            queryset = queryset.filter(class_name=class_name)
        if section:
            queryset = queryset.filter(section=section)

        return queryset

    def perform_create(self, serializer):
        parent_phone = serializer.validated_data.get('parent_phone')
        parent_user = User.objects.filter(phone=parent_phone).first()
        serializer.save(teacher=self.request.user, parent=parent_user)


class MarkViewSet(viewsets.ModelViewSet):
    serializer_class = MarkSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        queryset = Mark.objects.filter(student__teacher=user)
        
        subject = self.request.query_params.get('subject', None)
        exam_type = self.request.query_params.get('exam', None)
        
        if subject:
            queryset = queryset.filter(subject=subject)
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
            
        return queryset

    @action(detail=False, methods=['post'], url_path='save')
    def bulk_save(self, request):
        records = request.data.get('records', [])
        saved_count = 0
        errors = []
        for record in records:
            student_id = record.get('student')
            try:
                student = Student.objects.get(id=student_id, teacher=request.user)
                # Ensure we either create or update
                mark, created = Mark.objects.update_or_create(
                    student=student,
                    subject=record.get('subject'),
                    exam_type=record.get('exam_type'),
                    exam_date=record.get('exam_date'),
                    defaults={
                        'marks_obtained': record.get('marks_obtained'),
                        'max_marks': record.get('max_marks', 100.00),
                        'grade': record.get('grade')
                    }
                )
                saved_count += 1
            except Exception as e:
                errors.append(f"Student ID {student_id}: {str(e)}")
        
        if errors:
            return Response({"saved_count": saved_count, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": f"Successfully merged {saved_count} marks."}, status=status.HTTP_200_OK)


class FeeRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FeeRecordSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        return FeeRecord.objects.filter(student__teacher=user)

    @action(detail=False, methods=['post'], url_path='record-payment')
    def record_payment(self, request):
        student_id = request.data.get('student_id')
        amount_paid = request.data.get('amount_paid')
        date_paid = request.data.get('date', timezone.now().date())
        
        if not student_id or amount_paid is None:
            return Response({"error": "student_id and amount_paid are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            student = Student.objects.get(id=student_id, teacher=request.user)
            fee_record = FeeRecord.objects.filter(student=student, status='pending').first()
            if not fee_record:
                return Response({"error": "No pending fees found for student."}, status=status.HTTP_404_NOT_FOUND)
            
            fee_record.amount_paid += float(amount_paid)
            fee_record.last_payment_date = date_paid
            if fee_record.amount_paid >= fee_record.total_amount:
                fee_record.status = 'paid'
            elif fee_record.amount_paid > 0:
                fee_record.status = 'partial'
            fee_record.save()
            return Response({"message": "Payment recorded successfully", "new_paid_amount": fee_record.amount_paid}, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacher]    

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.filter(student__teacher=user)
        
        date = self.request.query_params.get('date', None)
        class_name = self.request.query_params.get('class', None)
        
        if date:
            queryset = queryset.filter(date=date)
        if class_name:
            queryset = queryset.filter(student__class_name=class_name)
            
        return queryset

    @action(detail=False, methods=['post'], url_path='bulk-mark')
    def bulk_mark(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            date = serializer.validated_data['date']
            records = serializer.validated_data['records']
            
            created_count = 0
            for record in records:
                student_id = record.get('student_id')
                is_present = record.get('is_present')
                
                # allow true/false boolean or string 'true'/'false'
                if is_present in ['true', 'True', True]:
                    state = True
                else:
                    state = False
                    
                if student_id:
                    # Enforce the caller's teacher mapping implicitly since they can't mark others' students
                    if Student.objects.filter(id=student_id, teacher=request.user).exists():
                        attendance, created = Attendance.objects.update_or_create(
                            date=date,
                            student_id=student_id,
                            defaults={
                                'is_present': state,
                                'marked_by': request.user
                            }
                        )
                        # Mock SMS if absent and parent exists
                        if not state and attendance.student.parent:
                            print(f"\n{'='*40}")
                            print("MOCK SMS SERVICE - ABSENT NOTIFICATION")
                            print(f"To: {attendance.student.parent.phone}")
                            print(f"Your child {attendance.student.full_name} was absent on {date}.")
                            print(f"{'='*40}\n")
                        created_count += 1
            return Response({"message": f"Successfully marked attendance for {created_count} students."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='stats/(?P<student_id>[^/.]+)')
    def stats(self, request, student_id=None):
        try:
            student = Student.objects.get(id=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        total_days = Attendance.objects.filter(student=student).count()
        present_days = Attendance.objects.filter(student=student, is_present=True).count()
        
        percentage = 0
        if total_days > 0:
            percentage = (present_days / total_days) * 100

        return Response({
            "student_id": student.id,
            "total_days": total_days,
            "present_days": present_days,
            "percentage": round(percentage, 2)
        })


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        # Assuming announcements created by teachers can only be viewed by them 
        # in the teacher portal.
        return Announcement.objects.all()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class ParentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'parent':
            return Response({"error": "Only parents can access this dashboard."}, status=status.HTTP_403_FORBIDDEN)
        
        students = Student.objects.filter(parent=request.user)
        students_data = []

        for student in students:
            # Attendance Stats
            total_days = Attendance.objects.filter(student=student).count()
            present_days = Attendance.objects.filter(student=student, is_present=True).count()
            att_percentage = (present_days / total_days * 100) if total_days > 0 else 0

            # Pending Fees
            pending_fees_aggregates = FeeRecord.objects.filter(
                student=student, status='pending'
            ).aggregate(
                total_amount_sum=Sum('total_amount'), 
                amount_paid_sum=Sum('amount_paid')
            )
            total_amount_sum = pending_fees_aggregates.get('total_amount_sum') or 0
            amount_paid_sum = pending_fees_aggregates.get('amount_paid_sum') or 0
            pending_fees = total_amount_sum - amount_paid_sum

            # Recent Marks
            recent_marks = Mark.objects.filter(student=student).order_by('-exam_date')[:5]
            marks_data = MarkSerializer(recent_marks, many=True).data

            student_data = dict(StudentSerializer(student).data)
            student_data['attendance_percentage'] = round(att_percentage, 2)
            student_data['pending_fees'] = float(pending_fees)
            student_data['recent_marks'] = marks_data
            
            students_data.append(student_data)

        # Announcements based on visibility and class matching
        announcement_ids = set()
        student_classes = set(student.class_name for student in students)
        student_ids = set(student.id for student in students)
        
        # All announcements
        all_announcements = Announcement.objects.all()
        for announcement in all_announcements:
            if announcement.visibility == 'all':
                announcement_ids.add(announcement.id)
            elif announcement.visibility == 'parents_only':
                announcement_ids.add(announcement.id)
            elif announcement.visibility == 'specific_class' and announcement.target_class in student_classes:
                announcement_ids.add(announcement.id)
            elif announcement.visibility == 'specific_student' and announcement.target_student_id in student_ids:
                announcement_ids.add(announcement.id)
        
        announcements = Announcement.objects.filter(id__in=announcement_ids).order_by('-created_at')[:10]
        announcements_data = AnnouncementSerializer(announcements, many=True).data

        return Response({
            "students": students_data,
            "announcements": announcements_data
        }, status=status.HTTP_200_OK)
