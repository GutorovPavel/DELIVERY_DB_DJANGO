from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('restaurants/<int:r_id>/<int:t_id>', Order.as_view(), name='restaurant'),
    path('profile/', profile, name='profile'),
    path('orders/', get_orders, name='orders'),
    path('restaurants/', Restaurants.as_view(), name='restaurants'),
    path('employees/', Employees.as_view(), name='employees'),
    path('profile/edit/<int:u_id>', edit_profile, name='edit'),
    path('sign/', sign, name='sign')
]