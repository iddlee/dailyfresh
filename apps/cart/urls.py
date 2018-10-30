from django.urls import path

from apps.cart.views import *

app_name = 'cart'
urlpatterns = [
    path('', cart, name='cart'),
]
