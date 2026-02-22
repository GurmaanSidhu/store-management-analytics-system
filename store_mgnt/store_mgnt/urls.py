"""
URL configuration for store_mgnt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib                 import admin
from django.urls                    import path, include
from app.views                      import hr_employee_list, product_list, create_sale, login_view, dashboard_view, add_product, sale_history, logout_view, ceo_dashboard, update_salary, hr_employee_list, adjust_inventory, check_in, check_out, view_shifts, product_list_api
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 

urlpatterns = [
    path('', login_view, name='login'),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    # path('api/products/', product_list, name='product-list'),
    path('api/sales/create/', create_sale),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('products/', product_list, name='products'),
    path('products/add/', add_product, name='add_product'),
    path('sales/create/', create_sale, name='create_sale'),
    path('sales/history/', sale_history, name='sale_history'),
    path('logout/', logout_view, name='logout'),
    path('ceo/', ceo_dashboard, name='ceo_dashboard'),
    path('hr/employees/', hr_employee_list, name='hr_employees'),
    path('hr/update/<int:user_id>/', update_salary, name='update_salary'),
    path('products/adjust/<int:product_id>/', adjust_inventory, name='adjust_inventory'),
    path('shift/checkin/', check_in, name='check_in'),
    path('shift/checkout/', check_out, name='check_out'),
    path('hr/shifts/', view_shifts, name='view_shifts'),
    path('api/products/', product_list_api, name='api_products'), 
    # path("manager/", manager_dashboard, name="manager_dashboard")  
]
