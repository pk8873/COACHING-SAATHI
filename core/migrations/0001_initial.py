# Generated initial migration for Coaching Saathi.
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Institute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="institute", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Batch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("course", models.CharField(blank=True, max_length=120)),
                ("schedule", models.CharField(blank=True, max_length=120)),
                ("monthly_fee", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="core.institute")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(max_length=30)),
                ("full_name", models.CharField(max_length=160)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("guardian_name", models.CharField(blank=True, max_length=160)),
                ("guardian_phone", models.CharField(blank=True, max_length=20)),
                ("monthly_fee", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("admission_date", models.DateField(default=django.utils.timezone.localdate)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="students", to="core.batch")),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="students", to="core.institute")),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.CreateModel(
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(default=django.utils.timezone.localdate)),
                ("status", models.CharField(choices=[("present", "Present"), ("absent", "Absent"), ("late", "Late"), ("leave", "Approved leave")], default="present", max_length=12)),
                ("note", models.CharField(blank=True, max_length=250)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="core.institute")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="core.student")),
            ],
            options={"ordering": ["-date", "student__full_name"]},
        ),
        migrations.CreateModel(
            name="FeePayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fee_month", models.DateField(help_text="Use the first day of the fee month.")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("method", models.CharField(choices=[("cash", "Cash"), ("upi", "UPI"), ("bank", "Bank transfer"), ("online", "Online"), ("other", "Other")], default="cash", max_length=10)),
                ("receipt_number", models.CharField(blank=True, max_length=40, unique=True)),
                ("paid_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("note", models.CharField(blank=True, max_length=250)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("institute", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="core.institute")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="core.student")),
            ],
            options={"ordering": ["-paid_at"]},
        ),
        migrations.AddConstraint(model_name="batch", constraint=models.UniqueConstraint(fields=("institute", "name"), name="unique_batch_name_per_institute")),
        migrations.AddConstraint(model_name="student", constraint=models.UniqueConstraint(fields=("institute", "student_id"), name="unique_student_id_per_institute")),
        migrations.AddConstraint(model_name="attendance", constraint=models.UniqueConstraint(fields=("student", "date"), name="unique_attendance_per_student_day")),
    ]
