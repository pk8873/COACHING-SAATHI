import csv
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import SignupForm, StudentForm, BatchForm, AttendanceForm, FeePaymentForm, InstituteForm
from .models import Institute, Student, Batch, Attendance, FeePayment

def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")

def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            Institute.objects.create(owner=user, name=form.cleaned_data["institute_name"], email=form.cleaned_data["email"])
            login(request, user)
            messages.success(request, "Welcome to Coaching Saathi. Your institute is ready.")
            return redirect("dashboard")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})

def _institute(request):
    try:
        return request.user.institute
    except Institute.DoesNotExist:
        return None

def _require_institute(request):
    institute = _institute(request)
    if not institute:
        messages.error(request, "Your account has no institute profile. Contact the administrator.")
        return None
    return institute

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
    recent_payments = payments.select_related("student")[:6]
    fee_due = Decimal("0.00")
    for student in students:
        paid = payments.filter(student=student, fee_month=month_start).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        fee_due += max(Decimal(student.monthly_fee) - paid, Decimal("0.00"))
    context = {
        "institute": institute, "student_count": students.count(),
        "batch_count": Batch.objects.filter(institute=institute, is_active=True).count(),
        "attendance_count": attendance_today.count(),
        "month_collection": month_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "fee_due": fee_due, "recent_payments": recent_payments,
        "attendance_present": attendance_today.filter(status="present").count(),
        "attendance_absent": attendance_today.filter(status="absent").count(),
    }
    return render(request, "dashboard.html", context)

@login_required
def students(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    qs = Student.objects.filter(institute=institute).select_related("batch")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "active")
    if query:
        from django.db.models import Q
        qs = qs.filter(Q(full_name__icontains=query) | Q(student_id__icontains=query) | Q(phone__icontains=query))
    if status == "active": qs = qs.filter(is_active=True)
    elif status == "archived": qs = qs.filter(is_active=False)
    return render(request, "students.html", {"institute": institute, "students": qs, "query": query, "status": status})

@login_required
def student_add(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    form = StudentForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.institute = institute
        try:
            obj.save()
        except Exception:
            form.add_error("student_id", "This student ID is already in use in your institute.")
        else:
            messages.success(request, "Student added successfully.")
            return redirect("students")
    return render(request, "form_page.html", {"form": form, "title": "Add student", "subtitle": "Create a student record", "institute": institute})

@login_required
def student_edit(request, pk):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    obj = get_object_or_404(Student, pk=pk, institute=institute)
    form = StudentForm(request.POST or None, instance=obj, institute=institute)
    if request.method == "POST" and form.is_valid():
        changed = form.save(commit=False); changed.institute = institute; changed.save()
        messages.success(request, "Student details updated.")
        return redirect("students")
    return render(request, "form_page.html", {"form": form, "title": "Edit student", "subtitle": obj.full_name, "institute": institute})

@login_required
def student_archive(request, pk):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    obj = get_object_or_404(Student, pk=pk, institute=institute)
    if request.method == "POST":
        obj.is_active = False; obj.save(update_fields=["is_active"])
        messages.success(request, "Student archived.")
    return redirect("students")

@login_required
def batches(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    form = BatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.institute = institute
        try: obj.save()
        except Exception: form.add_error("name", "A batch with this name already exists.")
        else:
            messages.success(request, "Batch created.")
            return redirect("batches")
    return render(request, "batches.html", {"institute": institute, "form": form, "batches": Batch.objects.filter(institute=institute), "student_counts": {b.pk: b.students.filter(is_active=True).count() for b in Batch.objects.filter(institute=institute)}})

@login_required
def attendance(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    form = AttendanceForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.institute = institute
        if Attendance.objects.filter(student=obj.student, date=obj.date).exists():
            form.add_error(None, "Attendance for this student and date is already recorded.")
        else:
            obj.save()
            messages.success(request, "Attendance saved.")
            return redirect("attendance")
    records = Attendance.objects.filter(institute=institute).select_related("student")[:100]
    return render(request, "attendance.html", {"institute": institute, "form": form, "records": records})

@login_required
def fees(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    form = FeePaymentForm(request.POST or None, institute=institute)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.institute = institute
        if obj.student.institute_id != institute.id:
            return HttpResponseForbidden("Invalid student.")
        obj.save()
        messages.success(request, f"Payment saved. Receipt: {obj.receipt_number}")
        return redirect("receipt", pk=obj.pk)
    payments = FeePayment.objects.filter(institute=institute).select_related("student")[:100]
    today = timezone.localdate()
    month_start = today.replace(day=1)
    total = FeePayment.objects.filter(institute=institute, paid_at__date__gte=month_start).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return render(request, "fees.html", {"institute": institute, "form": form, "payments": payments, "month_collection": total})

@login_required
def receipt(request, pk):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    payment = get_object_or_404(FeePayment.objects.select_related("student"), pk=pk, institute=institute)
    return render(request, "receipt.html", {"institute": institute, "payment": payment})

@login_required
def export_students(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="coaching-saathi-students.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student ID", "Full name", "Phone", "Guardian", "Guardian phone", "Batch", "Monthly fee", "Active"])
    for s in Student.objects.filter(institute=institute).select_related("batch"):
        writer.writerow([s.student_id, s.full_name, s.phone, s.guardian_name, s.guardian_phone, s.batch.name if s.batch else "", s.monthly_fee, s.is_active])
    return response

@login_required
def settings_view(request):
    institute = _require_institute(request)
    if not institute: return redirect("landing")
    form = InstituteForm(request.POST or None, instance=institute)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Institute settings saved.")
        return redirect("settings")
    return render(request, "form_page.html", {"form": form, "title": "Institute settings", "subtitle": "Manage your institute profile", "institute": institute})
