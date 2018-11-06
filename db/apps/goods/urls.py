from django.urls import path

from apps.goods.views import *

app_name = 'goods'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('detail/', DetailView.as_view(), name='detail')
]
