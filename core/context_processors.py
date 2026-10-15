from .models import Institute, StaffMembership


def workspace_role(request):
    role = None
    if request.user.is_authenticated:
        if Institute.objects.filter(owner=request.user).exists():
            role = "owner"
        else:
            membership = StaffMembership.objects.filter(user=request.user, is_active=True).first()
            role = membership.role if membership else None
    return {"workspace_role": role}
