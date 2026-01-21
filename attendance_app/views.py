from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Attendance
import datetime
from django.views.decorators.csrf import csrf_exempt

ALLOWED_IPS = ['127.0.0.1']  # Allowed IPs


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        ip = request.META.get('REMOTE_ADDR')
        if ip not in ALLOWED_IPS:
            return HttpResponse('IP Not Allowed')
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html')

@csrf_exempt
@login_required
def dashboard(request):
    today = datetime.date.today()
    
    # Get or create today's attendance
    attendance, created = Attendance.objects.get_or_create(
        employee=request.user,
        date=today,
        defaults={
            'day': today.strftime('%A'),
            'check_in': timezone.now(),
        }
    )

    # Mark late if after 9:30 AM
    if attendance.check_in.time() > datetime.time(9, 30):
        attendance.status = 'Late'
        attendance.save()

    context = {'attendance': attendance}

    # Superuser: show all attendance
    if request.user.is_superuser:
        all_attendance = Attendance.objects.all().order_by('date', 'check_in')
        context['all_attendance'] = all_attendance
        context['logged_in_users_count'] = all_attendance.count()

    return render(request, 'dashboard.html', context)

@csrf_exempt
@login_required
def logout_view(request):
    if request.method == 'POST':
        today = datetime.date.today()
        try:
            attendance = Attendance.objects.get(employee=request.user, date=today)
            attendance.check_out = timezone.now()
            attendance.save()
        except Attendance.DoesNotExist:
            pass
        logout(request)
        return redirect('login')
    else:
        # Prevent GET requests to logout
        return HttpResponse('Method not allowed', status=405)

@csrf_exempt
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.append(['Employee', 'Date', 'Day', 'Check In', 'Check Out', 'Status'])

    for a in Attendance.objects.all().order_by('date', 'check_in'):
        ws.append([
            a.employee.username,
            a.date.strftime('%Y-%m-%d'),
            a.day,
            a.check_in.strftime('%H:%M:%S') if a.check_in else '',
            a.check_out.strftime('%H:%M:%S') if a.check_out else '',
            a.status or ''
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance.xlsx'
    wb.save(response)
    return response
