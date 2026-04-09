import uuid
from django.db import models
from django.conf import settings


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=50)

    dob = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="students",
        limit_choices_to={"role": "teacher"}
    )

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"role": "parent"}
    )

    parent_name = models.CharField(max_length=255, blank=True)
    parent_phone = models.CharField(max_length=13, blank=True, null=True)

    subjects = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.class_name}-{self.section})"


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    date = models.DateField()
    is_present = models.BooleanField(default=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "date")

    def __str__(self):
        return f"{self.student.full_name} - {self.date}"

class Mark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    subject = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=255)

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)

    grade = models.CharField(max_length=2, blank=True, null=True)

    exam_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject}"
    
class FeeRecord(models.Model):
    STATUS_CHOICES = (
        ("paid", "Paid"),
        ("pending", "Pending"),
        ("partial", "Partial"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="fees"
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    due_date = models.DateField(blank=True, null=True)
    last_payment_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.status}"
    
class Announcement(models.Model):
    VISIBILITY_CHOICES = (
        ("all", "All"),
        ("parents_only", "Parents Only"),
        ("specific_class", "Specific Class"),
        ("specific_student", "Specific Student"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcements",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    target_class = models.CharField(max_length=100, blank=True, null=True)
    target_student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="private_announcements", null=True, blank=True
    )

    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
