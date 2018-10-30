import re

from django.core.mail import send_mail
from django.http import HttpResponse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.conf import settings


from apps.users.models import *


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
        subject = '欢迎来到【天天生鲜】，请验证您的邮箱'
        message = ''
        sender = settings.EMAIL_FROM
        receiver = [email]
        html_message = '<h1>你好，%s：</h1>感谢你成为【天天生鲜】成员，为了更好地使用本站提供的服务，请点击或访问以下链接验证您的邮箱(自发送邮件起一小时内有效)：<br><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a><br>如果您不是本站成员，请忽略此邮件。'%(username, token, token)

        send_mail(subject, message, sender, receiver, html_message=html_message)

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
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect(reverse('goods:index'))
        else:
            return render(request, 'login.html', {'errmsg': '账号或密码错误'})
