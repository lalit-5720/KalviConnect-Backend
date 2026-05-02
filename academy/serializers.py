from rest_framework import serializers
from .models import Student, Mark, FeeRecord, Attendance, Announcement
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentSerializer(serializers.ModelSerializer):
    attendance_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'full_name', 'class_name', 'section', 'parent_name', 'parent_phone', 'address', 'dob', 'photo_url', 'teacher', 'parent', 'subjects', 'created_at', 'attendance_percentage']
        read_only_fields = ['id', 'teacher', 'parent', 'created_at']

    def get_attendance_percentage(self, obj):
        from .models import Attendance
        total_days = Attendance.objects.filter(student=obj).count()
        present_days = Attendance.objects.filter(student=obj, is_present=True).count()
        return round((present_days / total_days * 100), 2) if total_days > 0 else 0.0



class MarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        required=False
    )
    student_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Mark
        fields = ['id', 'student', 'student_id', 'student_name', 'subject', 'exam_type', 'marks_obtained', 'max_marks', 'grade', 'exam_date', 'created_at']
        read_only_fields = ['id', 'created_at', 'student_name']

    def validate(self, data):
        # Handle student_id as an alternative to student
        student_id = data.pop('student_id', None)
        student = data.get('student')
        
        if student_id and not student:
            try:
                data['student'] = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"student_id": f"Student with ID {student_id} not found."})
        
        if not data.get('student'):
            raise serializers.ValidationError(
                {"student": "This field is required. Provide either 'student' (UUID) or 'student_id' (UUID)."}
            )
        
        if data.get('marks_obtained') is not None and data.get('max_marks') is not None:
            if data['marks_obtained'] > data['max_marks']:
                raise serializers.ValidationError({"marks_obtained": "Marks obtained cannot exceed max marks."})
        return data

class FeeRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        required=False
    )
    student_id = serializers.UUIDField(write_only=True, required=False)
    status = serializers.ChoiceField(choices=FeeRecord.STATUS_CHOICES, required=False)

    class Meta:
        model = FeeRecord
        fields = ['id', 'student', 'student_id', 'student_name', 'total_amount', 'amount_paid', 'status', 'due_date', 'last_payment_date', 'created_at']
        read_only_fields = ['id', 'created_at', 'student_name']

    def validate(self, data):
        # Handle student_id as an alternative to student
        student_id = data.pop('student_id', None)
        student = data.get('student')
        
        if student_id and not student:
            try:
                data['student'] = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"student_id": f"Student with ID {student_id} not found."})
        
        if not data.get('student'):
            raise serializers.ValidationError(
                {"student": "This field is required. Provide either 'student' (UUID) or 'student_id' (UUID)."}
            )
            
        if not data.get('status'):
            total = data.get('total_amount', 0)
            paid = data.get('amount_paid', 0)
            if float(paid) >= float(total):
                data['status'] = 'paid'
            elif float(paid) > 0:
                data['status'] = 'partial'
            else:
                data['status'] = 'pending'
        
        return data

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    marked_by = serializers.PrimaryKeyRelatedField(read_only=True)
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        required=False  # Make optional to allow student_id as alternative
    )
    student_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Attendance
        fields = ['id', 'date', 'student', 'student_id', 'student_name', 'is_present', 'marked_by', 'created_at']
        read_only_fields = ['id', 'created_at', 'marked_by', 'student_name']

    def validate(self, data):
        # Handle student_id as an alternative to student
        student_id = data.pop('student_id', None)
        student = data.get('student')
        
        if student_id and not student:
            # Try to fetch student by UUID
            try:
                data['student'] = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"student_id": f"Student with ID {student_id} not found."})
        
        if not data.get('student'):
            raise serializers.ValidationError(
                {"student": "This field is required. Provide either 'student' (UUID) or 'student_id' (UUID)."}
            )
        
        return data

class AttendanceRecordSerializer(serializers.Serializer):
    student_id = serializers.CharField()  # UUID as string
    is_present = serializers.BooleanField()

class BulkAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = serializers.ListField(
        child=AttendanceRecordSerializer()
    )

class AnnouncementSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    target_student_name = serializers.CharField(source='target_student.full_name', read_only=True)
    target_student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        required=False,
        allow_null=True
    )
    target_student_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Announcement
        fields = ['id', 'sender', 'sender_name', 'title', 'message', 'target_class', 'target_student', 'target_student_id', 'target_student_name', 'visibility', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender_name', 'target_student_name']

    def validate(self, data):
        ts_id = data.pop('target_student_id', None)
        ts = data.get('target_student')
        if ts_id and not ts:
            try:
                data['target_student'] = Student.objects.get(id=ts_id)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"target_student_id": "Target student not found."})
        return data
