from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    return render(request, 'dashboard/home.html', {'active_page': 'home'})


@login_required
def associates_view(request):
    return render(request, 'dashboard/associates.html', {'active_page': 'associates'})


@login_required
def vehicles_view(request):
    return render(request, 'dashboard/vehicles.html', {'active_page': 'vehicles'})


@login_required
def sms_center_view(request):
    return render(request, 'dashboard/sms_center.html', {'active_page': 'sms'})


@login_required
def import_review_view(request):
    """View for reviewing imported routes before sending SMS."""
    return render(request, 'dashboard/import_review.html', {'active_page': 'home'})
