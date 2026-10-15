from django.contrib import admin
from .models import Institute, Batch, Student, Attendance, FeePayment

admin.site.register(Institute)
admin.site.register(Batch)
admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(FeePayment)
