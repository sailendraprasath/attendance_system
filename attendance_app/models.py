
from django.db import models
from django.contrib.auth.models import User

class Attendance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    day = models.CharField(max_length=10)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Present')

    def __str__(self):
        return f"{self.employee.username} - {self.date}"