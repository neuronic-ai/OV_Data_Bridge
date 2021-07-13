from django.shortcuts import render
from django.views.generic.base import TemplateView


class LoginView(TemplateView):
    template_name = 'auth/login.html'


class SignupView(TemplateView):
    template_name = 'auth/signup.html'
