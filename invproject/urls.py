"""
URL configuration for invproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from main.views import add_inventory_item, inventory_list, stock_movement, stock_list, sensor_build, sensor_detail,generate_pdf, deployed_sensors, update_deployment_status,export_to_excel
from main.views_auth import login_view, logout_view, register_view, user_management, refresh_session
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/add/', add_inventory_item, name='add_inventory_item'),
    path('inventory-list/', inventory_list, name='inventory_list'),
    path('stock-movement/', stock_movement, name='stock_movement'),
    path('stock-list/', stock_list, name='stock_list'),
    path('sensor-build/', sensor_build, name='sensor_build'),
    path('sensor/<int:sensor_id>/', sensor_detail, name='sensor_detail'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('user-management/', user_management, name='user_management'),
    path('generate-pdf/', generate_pdf, name='generate_pdf'),
    path('deployed-sensors/', deployed_sensors, name='deployed_sensors'),
    path('update-deployment/<int:pk>/', update_deployment_status, name='update_deployment_status'),
    path('export-to-excel/', export_to_excel, name='export_to_excel'),
    path('refresh-session/', refresh_session, name='refresh_session'),
]
