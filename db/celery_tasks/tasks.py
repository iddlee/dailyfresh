# 使用celery
from celery import Celery

# 创建一个Celery类的实例对象
from django.core.mail import send_mail

from dailyfresh import settings

# 在任务处理者一端加以下几句代码,初始化django环境
'''
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()
'''

app = Celery('celery_tasks.tasks', broker='redis://10.12.153.104:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '欢迎来到【天天生鲜】，请验证您的邮箱'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>你好，%s：</h1>感谢您成为【天天生鲜】成员，为了更好地使用本站提供的服务，请点击或访问以下链接验证您的邮箱(自发送邮件起一小时内有效)：<br><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a><br>如果您不是本站成员，请忽略此邮件。' % (
    username, token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)


def generate_static_index_html():
    '''产生首页静态页面'''

