
from django.contrib import admin
from django.urls import path
from attendance_app.views import login_view, dashboard, logout_view, export_excel
# from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('export_excel/', export_excel, name='export_excel'),

]
