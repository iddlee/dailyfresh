from django.urls import path

from apps.orders.views import *

app_name = 'order'
urlpatterns = [
    path('place/', OrderPlaceView.as_view(), name='place')
]
