from django.contrib import admin
from .models import Institute, Batch, Student, Attendance, FeePayment, StaffMembership, PaymentOrder, Exam, ExamResult

admin.site.register([Institute, Batch, Student, Attendance, FeePayment, StaffMembership, PaymentOrder, Exam, ExamResult])
