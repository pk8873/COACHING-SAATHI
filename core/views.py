import csv
import os
import hmac
import hashlib
import json
from decimal import Decimal
from functools import wraps

import razorpay
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import (
    SignupForm, StaffCreateForm, StudentForm, BatchForm, AttendanceForm,
    FeePaymentForm, InstituteForm, ExamForm, ExamResultForm,
)
from .models import (
    Institute, StaffMembership, Student, Batch, Attendance, FeePayment,
    PaymentOrder, Exam, ExamResult,
)


def service_worker(request):
    from pathlib import Path
    source = Path(__file__).resolve().parent.parent / "static" / "pwa" / "sw.js"
    response = HttpResponse(source.read_text(encoding="utf-8"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Institute.objects.create(owner=user, name=form.cleaned_data["institute_name"], email=form.cleaned_data["email"])
        login(request, user)
        messages.success(request, "Welcome to Coaching Saathi. Your institute is ready.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


def _institute_for_user(user):
    if not user.is_authenticated:
        return None
    try:
        return user.institute
    except Institute.DoesNotExist:
        membership = StaffMembership.objects.filter(user=user, is_active=True).select_related("institute").first()
        return membership.institute if membership else None


def _role_for_user(user):
    if not user.is_authenticated:
        return None
    if Institute.objects.filter(owner=user).exists():
        return "owner"
    membership = StaffMembership.objects.filter(user=user, is_active=True).first()
    return membership.role if membership else None


def _require_institute(request):
    institute = _institute_for_user(request.user)
    if not institute:
        messages.error(request, "Your account has no active institute membership.")
    return institute


def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if _role_for_user(request.user) not in roles:
                return HttpResponseForbidden("Your staff role does not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


@login_required
def dashboard(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    today = timezone.localdate()
    month_start = today.replace(day=1)
    students = Student.objects.filter(institute=institute, is_active=True)
    payments = FeePayment.objects.filter(institute=institute)
    month_payments = payments.filter(paid_at__date__gte=month_start)
    attendance_today = Attendance.objects.filter(institute=institute, date=today)
    fee_due = Decimal("0.00")
    for student in students:
        paid = payments.filter(student=student, fee_month=month_start).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        fee_due += max(Decimal(student.monthly_fee) - paid, Decimal("0.00"))
    context = {
        "institute": institute, "role": _role_for_user(request.user),
        "student_count": students.count(),
        "batch_count": Batch.objects.filter(institute=institute, is_active=True).count(),
        "attendance_count": attendance_today.count(),
        "month_collection": month_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "fee_due": fee_due, "recent_payments": payments.select_related("student")[:6],
        "attendance_present": attendance_today.filter(status="present").count(),
        "attendance_absent": attendance_today.filter(status="absent").count(),
    }
    return render(request, "dashboard.html", context)


@login_required
@roles_required("owner", "admin", "teacher", "accountant")
def students(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    qs = Student.objects.filter(institute=institute).select_related("batch")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "active")
    if query:
        from django.db.models import Q
        qs = qs.filter(Q(full_name__icontains=query) | Q(student_id__icontains=query) | Q(phone__icontains=query))
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "archived":
        qs = qs.filter(is_active=False)
    return render(request, "students.html", {"institute": institute, "role": _role_for_user(request.user), "students": qs, "query": query, "status": status})


@login_required
@roles_required("owner", "admin", "teacher")
def student_add(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = StudentForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.institute = institute
        obj.save()
        messages.success(request, "Student added successfully.")
        return redirect("students")
    return render(request, "form_page.html", {"form": form, "title": "Add student", "subtitle": "Create a student record", "institute": institute, "role": _role_for_user(request.user)})


@login_required
@roles_required("owner", "admin", "teacher")
def student_edit(request, pk):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    obj = get_object_or_404(Student, pk=pk, institute=institute)
    form = StudentForm(request.POST or None, instance=obj, institute=institute)
    if request.method == "POST" and form.is_valid():
        changed = form.save(commit=False)
        changed.institute = institute
        changed.save()
        messages.success(request, "Student details updated.")
        return redirect("students")
    return render(request, "form_page.html", {"form": form, "title": "Edit student", "subtitle": obj.full_name, "institute": institute, "role": _role_for_user(request.user)})


@login_required
@roles_required("owner", "admin", "teacher")
def student_archive(request, pk):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    obj = get_object_or_404(Student, pk=pk, institute=institute)
    if request.method == "POST":
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        messages.success(request, "Student archived.")
    return redirect("students")


@login_required
@roles_required("owner", "admin", "teacher")
def batches(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = BatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.institute = institute
        obj.save()
        messages.success(request, "Batch created.")
        return redirect("batches")
    all_batches = Batch.objects.filter(institute=institute)
    return render(request, "batches.html", {"institute": institute, "role": _role_for_user(request.user), "form": form, "batches": all_batches, "student_counts": {b.pk: b.students.filter(is_active=True).count() for b in all_batches}})


@login_required
@roles_required("owner", "admin", "teacher")
def attendance(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = AttendanceForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.institute = institute
        if Attendance.objects.filter(student=obj.student, date=obj.date).exists():
            form.add_error(None, "Attendance for this student and date is already recorded.")
        else:
            obj.save()
            messages.success(request, "Attendance saved.")
            return redirect("attendance")
    records = Attendance.objects.filter(institute=institute).select_related("student")[:100]
    return render(request, "attendance.html", {"institute": institute, "role": _role_for_user(request.user), "form": form, "records": records})


def _razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


def _settle_online_order(order_id, payment_id):
    with transaction.atomic():
        order = PaymentOrder.objects.select_for_update().get(razorpay_order_id=order_id)
        if order.status == "paid":
            return FeePayment.objects.filter(
                institute=order.institute,
                note__contains=order.razorpay_order_id,
            ).first()
        payment = FeePayment.objects.create(
            institute=order.institute,
            student=order.student,
            fee_month=order.fee_month,
            amount=order.amount,
            method="online",
            note=f"Razorpay order {order.razorpay_order_id}; payment {payment_id}",
        )
        order.razorpay_payment_id = payment_id
        order.status = "paid"
        order.paid_at = timezone.now()
        order.save(update_fields=["razorpay_payment_id", "status", "paid_at"])
        return payment


@csrf_exempt
def razorpay_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not secret or not signature:
        return HttpResponse(status=400)
    expected = hmac.new(secret.encode("utf-8"), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return HttpResponse(status=400)
    try:
        payload = json.loads(request.body.decode("utf-8"))
        event = payload.get("event", "")
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id", "")
    except (ValueError, AttributeError, TypeError):
        return HttpResponse(status=400)
    if not order_id:
        return HttpResponse(status=200)
    order = PaymentOrder.objects.filter(razorpay_order_id=order_id).first()
    if not order:
        return HttpResponse(status=200)
    if event in ("payment.captured", "order.paid") and payment_id:
        _settle_online_order(order_id, payment_id)
    elif event == "payment.failed" and order.status != "paid":
        order.status = "failed"
        order.save(update_fields=["status"])
    return HttpResponse(status=200)


@login_required
@roles_required("owner", "admin", "accountant")
def fees(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = FeePaymentForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.institute = institute
        obj.save()
        messages.success(request, f"Payment saved. Receipt: {obj.receipt_number}")
        return redirect("receipt", pk=obj.pk)
    payments = FeePayment.objects.filter(institute=institute).select_related("student")[:100]
    today = timezone.localdate()
    month_start = today.replace(day=1)
    total = FeePayment.objects.filter(institute=institute, paid_at__date__gte=month_start).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    students_qs = Student.objects.filter(institute=institute, is_active=True)
    return render(request, "fees.html", {"institute": institute, "role": _role_for_user(request.user), "form": form, "payments": payments, "month_collection": total, "online_students": students_qs, "razorpay_enabled": bool(_razorpay_client())})


@login_required
@roles_required("owner", "admin", "accountant")
def online_payment_start(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    client = _razorpay_client()
    if not client:
        messages.error(request, "Online payment is not configured yet. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in Render environment variables.")
        return redirect("fees")
    if request.method != "POST":
        return redirect("fees")
    student = get_object_or_404(Student, pk=request.POST.get("student"), institute=institute, is_active=True)
    try:
        amount = Decimal(request.POST.get("amount", "0"))
        fee_month = parse_date(request.POST.get("fee_month", "")) or timezone.localdate()
    except Exception:
        messages.error(request, "Please enter a valid amount and fee month.")
        return redirect("fees")
    if amount <= 0 or amount > Decimal("1000000"):
        messages.error(request, "Amount must be greater than ₹0 and no more than ₹10,00,000.")
        return redirect("fees")
    fee_month = fee_month.replace(day=1)
    receipt = f"CS{institute.pk}{timezone.now():%y%m%d%H%M%S}"
    try:
        order_data = client.order.create(data={
            "amount": int(amount * 100), "currency": "INR", "receipt": receipt,
            "notes": {"institute_id": str(institute.pk), "student_id": str(student.pk), "fee_month": fee_month.isoformat()},
        })
    except Exception:
        messages.error(request, "Could not create a payment order. Check Razorpay test/live keys and try again.")
        return redirect("fees")
    order = PaymentOrder.objects.create(
        institute=institute, student=student, created_by=request.user, fee_month=fee_month,
        amount=amount, razorpay_order_id=order_data["id"],
    )
    return render(request, "payment_checkout.html", {
        "institute": institute, "role": _role_for_user(request.user), "order": order,
        "razorpay_key_id": os.getenv("RAZORPAY_KEY_ID", "").strip(),
        "amount_paise": int(order.amount * 100),
    })


@login_required
@roles_required("owner", "admin", "accountant")
def online_payment_verify(request):
    if request.method != "POST":
        return redirect("fees")
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    order = get_object_or_404(PaymentOrder, institute=institute, razorpay_order_id=order_id)
    if order.status == "paid":
        payment = FeePayment.objects.filter(institute=institute, note__contains=order.razorpay_order_id).first()
        return redirect("receipt", pk=payment.pk) if payment else redirect("fees")
    client = _razorpay_client()
    if not client:
        messages.error(request, "Payment verification is not configured.")
        return redirect("fees")
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except Exception:
        order.status = "failed"
        order.save(update_fields=["status"])
        messages.error(request, "Payment signature verification failed. No receipt was created.")
        return redirect("fees")
    payment = _settle_online_order(order.razorpay_order_id, payment_id)
    if not payment:
        messages.error(request, "Payment was verified, but a receipt could not be found. Please contact the institute.")
        return redirect("fees")
    messages.success(request, "Online payment verified successfully.")
    return redirect("receipt", pk=payment.pk)


@login_required
@roles_required("owner", "admin", "accountant")
def receipt(request, pk):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    payment = get_object_or_404(FeePayment.objects.select_related("student"), pk=pk, institute=institute)
    return render(request, "receipt.html", {"institute": institute, "role": _role_for_user(request.user), "payment": payment})


@login_required
@roles_required("owner", "admin", "teacher", "accountant")
def export_students(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="coaching-saathi-students.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student ID", "Full name", "Phone", "Guardian", "Guardian phone", "Batch", "Monthly fee", "Active"])
    for s in Student.objects.filter(institute=institute).select_related("batch"):
        writer.writerow([s.student_id, s.full_name, s.phone, s.guardian_name, s.guardian_phone, s.batch.name if s.batch else "", s.monthly_fee, s.is_active])
    return response


@login_required
@roles_required("owner", "admin")
def staff(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        StaffMembership.objects.create(institute=institute, user=user, role=form.cleaned_data["role"])
        messages.success(request, f"Staff account {user.username} created.")
        return redirect("staff")
    members = StaffMembership.objects.filter(institute=institute, is_active=True).select_related("user")
    return render(request, "staff.html", {"institute": institute, "role": _role_for_user(request.user), "form": form, "members": members})


@login_required
@roles_required("owner", "admin")
def staff_deactivate(request, pk):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    member = get_object_or_404(StaffMembership, pk=pk, institute=institute)
    if request.method == "POST":
        member.is_active = False
        member.save(update_fields=["is_active"])
        messages.success(request, f"Access disabled for {member.user.username}.")
    return redirect("staff")


@login_required
@roles_required("owner", "admin", "teacher")
def exams(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = ExamForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        exam = form.save(commit=False)
        exam.institute = institute
        exam.created_by = request.user
        exam.save()
        messages.success(request, "Exam created. Add student results from the exam list.")
        return redirect("exams")
    items = Exam.objects.filter(institute=institute).select_related("batch").annotate(result_count=Count("results"))
    return render(request, "exams.html", {"institute": institute, "role": _role_for_user(request.user), "form": form, "exams": items})


@login_required
@roles_required("owner", "admin", "teacher")
def exam_results(request, pk):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    exam = get_object_or_404(Exam, pk=pk, institute=institute)
    form = ExamResultForm(request.POST or None, exam=exam, institute=institute)
    if request.method == "POST" and form.is_valid():
        result = form.save(commit=False)
        result.exam = exam
        if ExamResult.objects.filter(exam=exam, student=result.student).exists():
            form.add_error("student", "A result for this student already exists. Use the edit option in a future update.")
        else:
            result.save()
            messages.success(request, "Result saved.")
            return redirect("exam_results", pk=exam.pk)
    results = exam.results.select_related("student")
    average = results.aggregate(avg=Avg("marks_obtained"))["avg"] or Decimal("0.00")
    return render(request, "exam_results.html", {"institute": institute, "role": _role_for_user(request.user), "exam": exam, "form": form, "results": results, "average": average})


@login_required
@roles_required("owner", "admin", "accountant")
def reports(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    today = timezone.localdate()
    start = parse_date(request.GET.get("from", "")) or today.replace(day=1)
    end = parse_date(request.GET.get("to", "")) or today
    if start > end:
        start, end = end, start
    payments = FeePayment.objects.filter(institute=institute, paid_at__date__gte=start, paid_at__date__lte=end)
    attendance_qs = Attendance.objects.filter(institute=institute, date__gte=start, date__lte=end)
    result_qs = ExamResult.objects.filter(exam__institute=institute, exam__exam_date__gte=start, exam__exam_date__lte=end)
    monthly = payments.annotate(month=TruncMonth("paid_at")).values("month").annotate(total=Sum("amount"), count=Count("id")).order_by("month")
    context = {
        "institute": institute, "role": _role_for_user(request.user), "start": start, "end": end,
        "collection": payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "payment_count": payments.count(), "attendance_count": attendance_qs.count(),
        "present_count": attendance_qs.filter(status="present").count(),
        "absent_count": attendance_qs.filter(status="absent").count(),
        "exam_count": Exam.objects.filter(institute=institute, exam_date__gte=start, exam_date__lte=end).count(),
        "result_count": result_qs.count(),
        "average_marks": result_qs.aggregate(avg=Avg("marks_obtained"))["avg"] or Decimal("0.00"),
        "monthly": monthly, "recent_payments": payments.select_related("student")[:100],
    }
    return render(request, "reports.html", context)


@login_required
@roles_required("owner", "admin", "accountant")
def export_report(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    today = timezone.localdate()
    start = parse_date(request.GET.get("from", "")) or today.replace(day=1)
    end = parse_date(request.GET.get("to", "")) or today
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="coaching-saathi-financial-report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Receipt", "Student ID", "Student", "Fee month", "Paid at", "Method", "Amount", "Note"])
    for p in FeePayment.objects.filter(institute=institute, paid_at__date__gte=start, paid_at__date__lte=end).select_related("student"):
        writer.writerow([p.receipt_number, p.student.student_id, p.student.full_name, p.fee_month, p.paid_at, p.get_method_display(), p.amount, p.note])
    return response


@login_required
@roles_required("owner", "admin")
def settings_view(request):
    institute = _require_institute(request)
    if not institute:
        return redirect("landing")
    form = InstituteForm(request.POST or None, instance=institute)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Institute settings saved.")
        return redirect("settings")
    return render(request, "form_page.html", {"form": form, "title": "Institute settings", "subtitle": "Manage your institute profile", "institute": institute, "role": _role_for_user(request.user)})
