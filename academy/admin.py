from django.contrib import admin
from .models import Student, Attendance, Mark, FeeRecord, Announcement

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'class_name', 'section', 'teacher', 'parent_phone')
    search_fields = ('full_name', 'parent_phone')
    list_filter = ('class_name', 'section')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'is_present', 'marked_by')
    list_filter = ('date', 'is_present')
    search_fields = ('student__full_name',)

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam_type', 'marks_obtained', 'max_marks')
    list_filter = ('subject', 'exam_type')
    search_fields = ('student__full_name',)

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_amount', 'amount_paid', 'status')
    list_filter = ('status',)
    search_fields = ('student__full_name',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'visibility', 'created_at')
    list_filter = ('visibility',)
