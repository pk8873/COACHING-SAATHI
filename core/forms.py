from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Institute, Student, Batch, Attendance, FeePayment

class SignupForm(UserCreationForm):
    institute_name = forms.CharField(max_length=160, label="Coaching institute name")
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ("username", "email", "institute_name", "password1", "password2")

class InstituteForm(forms.ModelForm):
    class Meta:
        model = Institute
        fields = ("name", "phone", "email", "address")

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("student_id", "full_name", "phone", "email", "guardian_name", "guardian_phone", "batch", "monthly_fee", "admission_date", "is_active", "notes")
        widgets = {"admission_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}
    def __init__(self, *args, institute=None, **kwargs):
        super().__init__(*args, **kwargs)
        if institute:
            self.fields["batch"].queryset = Batch.objects.filter(institute=institute, is_active=True)
        self.fields["batch"].required = False

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ("name", "course", "schedule", "monthly_fee", "is_active")

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ("student", "date", "status", "note")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
    def __init__(self, *args, institute=None, **kwargs):
        super().__init__(*args, **kwargs)
        if institute:
            self.fields["student"].queryset = Student.objects.filter(institute=institute, is_active=True)

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ("student", "fee_month", "amount", "method", "note")
        widgets = {"fee_month": forms.DateInput(attrs={"type": "date"})}
    def __init__(self, *args, institute=None, **kwargs):
        super().__init__(*args, **kwargs)
        if institute:
            self.fields["student"].queryset = Student.objects.filter(institute=institute, is_active=True)
        self.fields["amount"].widget.attrs.update({"min": "0.01", "step": "0.01"})
    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount
    def clean_fee_month(self):
        date = self.cleaned_data["fee_month"]
        return date.replace(day=1)
