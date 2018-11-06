from django.shortcuts import render
from django.views import View

from utils.mixin import LoginRequiresMixin


class CartView(LoginRequiresMixin, View):
    def get(self, request):
        return render(request, 'cart.html')
