from django.contrib.auth.decorators import login_required
from django.urls import path

from apps.users.views import *

app_name = 'user'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('active/<token>/', ActiveView.as_view(), name='active'),  # 用户激活
    path('', UserInfoView.as_view(), name='user'),
    path('order/<page>/', UserOrderView.as_view(), name='order'),
    path('address/', AddressView.as_view(), name='address'),
]

'''
以下为在不使用统一封装的mixin时，路由的方式
# path('', login_required(UserInfoView.as_view()), name='user'),
# path('order/', login_required(UserOrderView.as_view()), name='order'),
# path('address/', login_required(AddressView.as_view()), name='address'),
'''
