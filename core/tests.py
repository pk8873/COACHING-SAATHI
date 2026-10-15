from decimal import Decimal
import hashlib
import hmac
import json
import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ExamResultForm
from .models import Attendance, FeePayment, Institute, Student, StaffMembership, Exam, PaymentOrder


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



class StaffRoleTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="ownerrole", password="Strong-password-123")
        self.institute = Institute.objects.create(owner=self.owner, name="Role Test Institute")
        self.teacher = User.objects.create_user(username="teacherrole", password="Strong-password-123")
        self.accountant = User.objects.create_user(username="accountantrole", password="Strong-password-123")
        StaffMembership.objects.create(institute=self.institute, user=self.teacher, role="teacher")
        StaffMembership.objects.create(institute=self.institute, user=self.accountant, role="accountant")

    def test_teacher_can_access_exams(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exams"))
        self.assertEqual(response.status_code, 200)

    def test_accountant_cannot_access_exam_management(self):
        self.client.force_login(self.accountant)
        response = self.client.get(reverse("exams"))
        self.assertEqual(response.status_code, 403)

    def test_accountant_can_access_fee_page(self):
        self.client.force_login(self.accountant)
        response = self.client.get(reverse("fees"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_manage_staff(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("staff"))
        self.assertEqual(response.status_code, 403)


class ExamResultValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="examowner", password="Strong-password-123")
        self.institute = Institute.objects.create(owner=self.owner, name="Exam Institute")
        self.student = Student.objects.create(institute=self.institute, student_id="EX001", full_name="Test Learner")
        self.exam = Exam.objects.create(
            institute=self.institute, title="Maths Test",
            exam_date=timezone.localdate(), max_marks=Decimal("50.00"), created_by=self.owner,
        )

    def test_marks_cannot_exceed_exam_maximum(self):
        form = ExamResultForm(
            data={"student": self.student.pk, "marks_obtained": "51", "remarks": ""},
            exam=self.exam, institute=self.institute,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("marks_obtained", form.errors)

    def test_marks_within_maximum_are_valid(self):
        form = ExamResultForm(
            data={"student": self.student.pk, "marks_obtained": "45", "remarks": "Good"},
            exam=self.exam, institute=self.institute,
        )
        self.assertTrue(form.is_valid())



class RazorpayWebhookTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="payowner", password="Strong-password-123")
        self.institute = Institute.objects.create(owner=self.owner, name="Payment Test Institute")
        self.student = Student.objects.create(
            institute=self.institute, student_id="PAY001", full_name="Payment Learner"
        )
        self.order = PaymentOrder.objects.create(
            institute=self.institute, student=self.student, created_by=self.owner,
            fee_month=timezone.localdate().replace(day=1), amount=Decimal("500.00"),
            razorpay_order_id="order_test_123",
        )

    def test_signed_capture_webhook_creates_one_receipt_even_if_retried(self):
        secret = "test-webhook-secret"
        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {
                "id": "pay_test_123", "order_id": self.order.razorpay_order_id
            }}},
        }
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        with patch.dict(os.environ, {"RAZORPAY_WEBHOOK_SECRET": secret}):
            for _ in range(2):
                response = self.client.post(
                    reverse("razorpay_webhook"), data=body,
                    content_type="application/json",
                    HTTP_X_RAZORPAY_SIGNATURE=signature,
                )
                self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(FeePayment.objects.filter(institute=self.institute).count(), 1)

    def test_invalid_webhook_signature_is_rejected(self):
        with patch.dict(os.environ, {"RAZORPAY_WEBHOOK_SECRET": "expected-secret"}):
            response = self.client.post(
                reverse("razorpay_webhook"), data=b'{"event":"payment.captured"}',
                content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE="invalid",
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(FeePayment.objects.count(), 0)
