import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StaffMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("admin", "Administrator"), ("teacher", "Teacher"), ("accountant", "Accountant")], default="teacher", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_memberships", to="core.institute")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coaching_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("institute", "user"), name="unique_staff_membership")]},
        ),
        migrations.CreateModel(
            name="PaymentOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fee_month", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("razorpay_order_id", models.CharField(max_length=80, unique=True)),
                ("razorpay_payment_id", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")], default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_payment_orders", to=settings.AUTH_USER_MODEL)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payment_orders", to="core.institute")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_orders", to="core.student")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Exam",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("exam_date", models.DateField(default=django.utils.timezone.localdate)),
                ("max_marks", models.DecimalField(decimal_places=2, default=100, max_digits=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="exams", to="core.batch")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_exams", to=settings.AUTH_USER_MODEL)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exams", to="core.institute")),
            ],
            options={"ordering": ["-exam_date", "title"]},
        ),
        migrations.CreateModel(
            name="ExamResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("marks_obtained", models.DecimalField(decimal_places=2, max_digits=8)),
                ("remarks", models.CharField(blank=True, max_length=250)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="core.exam")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_results", to="core.student")),
            ],
            options={"ordering": ["-marks_obtained", "student__full_name"], "constraints": [models.UniqueConstraint(fields=("exam", "student"), name="unique_result_per_exam_student")]},
        ),
    ]
