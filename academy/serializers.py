from rest_framework import serializers
from .models import Student, Mark, FeeRecord, Attendance, Announcement
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'full_name', 'class_name', 'section', 'parent_name', 'parent_phone', 'address', 'dob', 'photo_url', 'teacher', 'parent', 'subjects', 'created_at']
        read_only_fields = ['id', 'teacher', 'parent', 'created_at']



class MarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Mark
        fields = ['id', 'student', 'student_name', 'subject', 'exam_type', 'marks_obtained', 'max_marks', 'grade', 'exam_date', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        if data.get('marks_obtained') is not None and data.get('max_marks') is not None:
            if data['marks_obtained'] > data['max_marks']:
                raise serializers.ValidationError({"marks_obtained": "Marks obtained cannot exceed max marks."})
        return data

class FeeRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = FeeRecord
        fields = ['id', 'student', 'student_name', 'total_amount', 'amount_paid', 'status', 'due_date', 'last_payment_date', 'created_at']
        read_only_fields = ['id', 'created_at']

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    marked_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'date', 'student', 'student_name', 'is_present', 'marked_by', 'created_at']
        read_only_fields = ['id', 'created_at', 'marked_by']

class BulkAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = serializers.ListField(
        child=serializers.DictField()
    )

class AnnouncementSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'sender', 'sender_name', 'title', 'message', 'target_class', 'target_student', 'visibility', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender_name']
