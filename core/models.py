from django.conf import settings
from django.db import models
from django.utils import timezone

class Institute(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="institute")
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Batch(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="batches")
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=120, blank=True)
    schedule = models.CharField(max_length=120, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["institute", "name"], name="unique_batch_name_per_institute")]
    def __str__(self):
        return self.name

class Student(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="students")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    student_id = models.CharField(max_length=30)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    guardian_name = models.CharField(max_length=160, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admission_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["full_name"]
        constraints = [models.UniqueConstraint(fields=["institute", "student_id"], name="unique_student_id_per_institute")]
    def __str__(self):
        return f"{self.student_id} — {self.full_name}"

class Attendance(models.Model):
    STATUS_CHOICES = [("present", "Present"), ("absent", "Absent"), ("late", "Late"), ("leave", "Approved leave")]
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="present")
    note = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-date", "student__full_name"]
        constraints = [models.UniqueConstraint(fields=["student", "date"], name="unique_attendance_per_student_day")]

class FeePayment(models.Model):
    METHOD_CHOICES = [("cash", "Cash"), ("upi", "UPI"), ("bank", "Bank transfer"), ("online", "Online"), ("other", "Other")]
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="payments")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="payments")
    fee_month = models.DateField(help_text="Use the first day of the fee month.")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="cash")
    receipt_number = models.CharField(max_length=40, unique=True, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-paid_at"]
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from uuid import uuid4
            self.receipt_number = "CS-" + uuid4().hex[:12].upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.receipt_number} — {self.student.full_name}"
