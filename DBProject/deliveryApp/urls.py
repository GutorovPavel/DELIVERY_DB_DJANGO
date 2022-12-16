from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('restaurants/<int:r_id>/<int:t_id>', Order.as_view(), name='restaurant'),
    path('sign/', sign, name='sign')
]