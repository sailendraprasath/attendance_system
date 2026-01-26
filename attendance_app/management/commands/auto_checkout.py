from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from attendance_app.models import Attendance


class Command(BaseCommand):
    help = 'Auto checkout employees at 6:15 PM'

    def handle(self, *args, **kwargs):
        today = datetime.date.today()
        checkout_time = timezone.make_aware(
            datetime.datetime.combine(today, datetime.time(18, 15))
        )

        records = Attendance.objects.filter(
            date=today,
            check_out__isnull=True,
            employee__is_superuser=False
        )

        for att in records:
            att.check_out = checkout_time
            att.save()

        self.stdout.write("Auto checkout done")