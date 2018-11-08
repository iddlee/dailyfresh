from django.urls import path

from apps.cart.views import *

app_name = 'cart'
urlpatterns = [
    path('', CartInfoView.as_view(), name='cart'),
    path('add/', CartAddView.as_view(), name='add'),  # 购物车记录添加
    path('update/', CartUpdateView.as_view(), name='update'),  # 购物车记录更新
    path('delete/', CartDeleteView.as_view(), name='delete'),  # 删除购物车记录

]
