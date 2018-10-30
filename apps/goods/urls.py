from django.urls import path

from apps.goods.views import *

app_name = 'goods'
urlpatterns = [
    path('', index, name='index'),
    path('detail/', detail, name='detail')
]
