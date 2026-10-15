from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
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
    path("fees/<int:pk>/receipt/", views.receipt, name="receipt"),
    path("reports/students.csv", views.export_students, name="export_students"),
    path("settings/", views.settings_view, name="settings"),
]
