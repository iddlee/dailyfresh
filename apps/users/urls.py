from django.urls import path

from apps.users.views import *

app_name = 'user'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('active/<token>/', ActiveView.as_view(), name='active'),  # 用户激活
]
