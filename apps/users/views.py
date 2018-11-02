import re

from django.core.mail import send_mail
from django.http import HttpResponse
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.conf import settings


from apps.users.models import *
from apps.goods.models import *
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiresMixin


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '信息不能为空'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意“天天生鲜用户使用协议”'})
        if password != cpwd:
            return render(request, 'register.html', {'errmsg': '两次输入的密码不一致'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        user = User.objects.create_user(username=username, password=password, email=email)
        user.is_active = 0
        user.save()

        # 加密用户身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf8')

        # 发邮件
        send_register_active_email.delay(email, username, token)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        # 解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活待激活用户的id
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活连接已过期')


class LoginView(View):
    def get(self, request):
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '信息缺失，不合法'})
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                # 获取登陆后所要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))  # 如果是正常登录，网址后没有next，默认跳转首页
                response = redirect(next_url)
                # 判断用户是否勾选记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', user.username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活，请到注册邮箱激活'})
        else:
            return render(request, 'login.html', {'errmsg': '账号或密码错误'})


class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiresMixin, View):
    '''用户中心信息'''
    def get(self, request):
        # 获取用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # StrictRedis(host='10.12.153.104', port='6379', db=9)
        con = get_redis_connection("default")

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiresMixin, View):
    '''用户中心订单'''
    def get(self, request):
        # 获取用户的订单信息
        return render(request, 'user_center_order.html', {'page': 'order'})


class AddressView(LoginRequiresMixin, View):
    '''用户中心地址'''
    def get(self, request):
        # 获取用户的默认收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在收获地址
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 添加地址
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '收货信息不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '请输入正确的手机号码'})
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应的User对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在收获地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True
        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)

        return redirect(reverse('user:address'))
