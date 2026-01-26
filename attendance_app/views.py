from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Attendance
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

ALLOWED_IPS = ['127.0.0.1']  # Allowed IPs


# ================= LOGIN =================
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


# ================= DASHBOARD =================
@login_required
def dashboard(request):
    today = datetime.date.today()
    context = {
        'attendance': None,       # for normal users
        'all_attendance': [],     # for superuser
        'analytics': {}           # superuser analytics
    }

    # NORMAL USER
    if not request.user.is_superuser:
        now = timezone.localtime(timezone.now())
        check_in_limit = datetime.time(10, 15)

        attendance, created = Attendance.objects.get_or_create(
            employee=request.user,
            date=today,
            defaults={
                'day': today.strftime('%A'),
                'check_in': now,
                'status': 'Present'
            }
        )

        # If login after 10:15 → Absent
        if created and now.time() > check_in_limit:
            attendance.status = 'Absent'
            attendance.save()

        context['attendance'] = attendance

    # SUPERUSER
    if request.user.is_superuser:
        all_attendance = Attendance.objects.filter(
            employee__is_superuser=False
        ).order_by('date', 'check_in')
        context['all_attendance'] = all_attendance

        # Analytics precomputed
        context['analytics'] = {
            'total': all_attendance.count(),
            'present': all_attendance.filter(status='Present').count(),
            'late': all_attendance.filter(status='Late').count(),
            'absent': all_attendance.filter(status='Absent').count(),
        }

    return render(request, 'dashboard.html', context)


# ================= LOGOUT =================

@csrf_exempt
@login_required
def logout_view(request):
    if request.method == 'POST':
        if not request.user.is_superuser:
            today = datetime.date.today()
            try:
                attendance = Attendance.objects.get(
                    employee=request.user,
                    date=today
                )

                # Save actual logout time
                if not attendance.check_out:
                    attendance.check_out = timezone.localtime(timezone.now())
                    attendance.save()

            except Attendance.DoesNotExist:
                pass

        logout(request)
        return redirect('login')

    return HttpResponse('Method not allowed', status=405)

# ================= EXPORT EXCEL =================
@csrf_exempt
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.append(['Employee', 'Date', 'Day', 'Check In', 'Check Out', 'Status'])

    for a in Attendance.objects.filter(employee__is_superuser=False).order_by('date', 'check_in'):
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


# ================= EDIT ATTENDANCE =================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_attendance(request, pk):
    att = get_object_or_404(Attendance, id=pk)
    if request.method == 'POST':
        att.status = request.POST.get('status', att.status)
        
        check_in_str = request.POST.get('check_in', '')
        check_out_str = request.POST.get('check_out', '')

        if check_in_str:
            dt = parse_datetime(check_in_str)
            if dt:
                att.check_in = dt

        if check_out_str:
            dt = parse_datetime(check_out_str)
            if dt:
                att.check_out = dt

        att.save()
        return redirect('dashboard')

    return render(request, 'edit_attendance.html', {'attendance': att})

# ================= DELETE ATTENDANCE =================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_attendance(request, pk):
    att = get_object_or_404(Attendance, id=pk)
    att.delete()
    return redirect('dashboard')
