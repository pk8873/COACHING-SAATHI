from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Institute, Student, Batch, Attendance, FeePayment
from decimal import Decimal

class TenantIsolationTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="owner1", password="Strong-password-123")
        self.user2 = User.objects.create_user(username="owner2", password="Strong-password-123")
        self.i1 = Institute.objects.create(owner=self.user1, name="Institute One")
        self.i2 = Institute.objects.create(owner=self.user2, name="Institute Two")
        self.student = Student.objects.create(institute=self.i1, student_id="S001", full_name="Student One", monthly_fee=Decimal("1000"))
        self.client = Client()
        self.client.force_login(self.user2)

    def test_cannot_edit_other_institute_student(self):
        response = self.client.get(reverse("student_edit", args=[self.student.pk]))
        self.assertEqual(response.status_code, 404)

    def test_student_list_is_tenant_scoped(self):
        response = self.client.get(reverse("students"))
        self.assertNotContains(response, "Student One")

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
