from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("sw.js", views.service_worker, name="service_worker"),
    path("", views.landing, name="landing"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("students/", views.students, name="students"),
    path("students/add/", views.student_add, name="student_add"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/archive/", views.student_archive, name="student_archive"),
    path("batches/", views.batches, name="batches"),
    path("attendance/", views.attendance, name="attendance"),
    path("fees/", views.fees, name="fees"),
    path("fees/online/start/", views.online_payment_start, name="online_payment_start"),
    path("fees/online/verify/", views.online_payment_verify, name="online_payment_verify"),
    path("webhooks/razorpay/", views.razorpay_webhook, name="razorpay_webhook"),
    path("fees/<int:pk>/receipt/", views.receipt, name="receipt"),
    path("staff/", views.staff, name="staff"),
    path("staff/<int:pk>/deactivate/", views.staff_deactivate, name="staff_deactivate"),
    path("exams/", views.exams, name="exams"),
    path("exams/<int:pk>/results/", views.exam_results, name="exam_results"),
    path("reports/", views.reports, name="reports"),
    path("reports/export.csv", views.export_report, name="export_report"),
    path("reports/students.csv", views.export_students, name="export_students"),
    path("settings/", views.settings_view, name="settings"),
]
