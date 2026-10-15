from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Attendance, FeePayment, Institute, Student


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="owner1", password="Strong-password-123"
        )
        self.user2 = User.objects.create_user(
            username="owner2", password="Strong-password-123"
        )
        self.i1 = Institute.objects.create(owner=self.user1, name="Institute One")
        self.i2 = Institute.objects.create(owner=self.user2, name="Institute Two")
        self.student = Student.objects.create(
            institute=self.i1,
            student_id="S001",
            full_name="Student One",
            monthly_fee=Decimal("1000.00"),
        )
        self.client = Client()
        self.client.force_login(self.user2)

    def test_cannot_edit_other_institute_student(self):
        response = self.client.get(reverse("student_edit", args=[self.student.pk]))
        self.assertEqual(response.status_code, 404)

    def test_student_list_is_tenant_scoped(self):
        response = self.client.get(reverse("students"))
        self.assertNotContains(response, "Student One")

    def test_cannot_view_other_institute_receipt(self):
        payment = FeePayment.objects.create(
            institute=self.i1,
            student=self.student,
            fee_month=timezone.localdate().replace(day=1),
            amount=Decimal("1000.00"),
        )
        response = self.client.get(reverse("receipt", args=[payment.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_record_fee_for_another_institute_student(self):
        response = self.client.post(
            reverse("fees"),
            {
                "student": self.student.pk,
                "fee_month": timezone.localdate().replace(day=1).isoformat(),
                "amount": "1000.00",
                "method": "cash",
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_cannot_record_attendance_for_another_institute_student(self):
        response = self.client.post(
            reverse("attendance"),
            {
                "student": self.student.pk,
                "date": timezone.localdate().isoformat(),
                "status": "present",
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class SignupTests(TestCase):
    def test_signup_creates_user_and_institute(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newowner",
                "email": "owner@example.com",
                "institute_name": "New Coaching Centre",
                "password1": "A-very-strong-password-2046",
                "password2": "A-very-strong-password-2046",
            },
            follow=True,
        )
        self.assertTrue(User.objects.filter(username="newowner").exists())
        user = User.objects.get(username="newowner")
        self.assertEqual(user.institute.name, "New Coaching Centre")
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.redirect_chain[-1][0], reverse("dashboard"))
