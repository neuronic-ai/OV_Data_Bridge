from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
import time

from db.models import (
    TBLUser,
)


class LoginView(TemplateView):
    template_name = 'auth/login.html'

    def post(self, *args, **kwargs):
        user = authenticate(username=self.request.POST['username'], password=self.request.POST['password'])
        if user:
            django_login(self.request, user)
            return redirect('/data_bridges')
        else:
            time.sleep(0.5)
            return render(self.request, self.template_name, {
                'alert': 'These credentials do not match our records.'
            })


def logout(request):
    django_logout(request)
    return redirect('/')


class SignupView(TemplateView):
    template_name = 'auth/signup.html'

    def post(self, *args, **kwargs):
        email = self.request.POST['email']
        username = self.request.POST['username']
        password = self.request.POST['password']

        # check if email is already registered
        if TBLUser.objects.filter(username=username).exists() or TBLUser.objects.filter(email=email).exists():
            return render(self.request, self.template_name, {
                'alert': 'This username or email is already registered.'
            })

        user = TBLUser()
        user.email = email
        user.username = username
        user.set_password(password)
        user.save()

        django_login(self.request, user)
        return redirect('/data_bridges')


class PasswordResetView(TemplateView):
    template_name = 'auth/password_reset.html'

    def post(self, *args, **kwargs):
        email = self.request.POST['email']

        return render(self.request, self.template_name, {
            'success': 'An email with a link to reset your password was sent to your email.'
        })
