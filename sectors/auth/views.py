from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.http import HttpResponse
import time
import json

from sectors.common import admin_config, error, mail, common

from db.models import (
    TBLUser,
    TBLSetting,
    TBLTransaction,
)


class LoginView(TemplateView):
    template_name = 'auth/login.html'

    def post(self, *args, **kwargs):
        user = authenticate(username=self.request.POST['username'], password=self.request.POST['password'])
        if user:
            django_login(self.request, user)
            return redirect('/data_bridges')
        else:
            time.sleep(admin_config.DELAY_FOR_BAD_REQUEST)
            return render(self.request, self.template_name, {
                'alert': error.WRONG_CREDENTIAL
            })


def logout(request):
    django_logout(request)
    return redirect('/')


class SignupView(TemplateView):
    template_name = 'auth/signup.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SignupView, self).get_context_data(*args, **kwargs)
        context['terms_of_service'] = '#'
        setting = list(TBLSetting.objects.all().values())
        if len(setting):
            setting = setting[0]
            context['terms_of_service'] = setting['server_setting']['user_link']

        return context

    def post(self, *args, **kwargs):
        email = self.request.POST['email']
        username = self.request.POST['username']
        password = self.request.POST['password']

        # check if email is already registered
        if TBLUser.objects.filter(username=username).exists() or TBLUser.objects.filter(email=email).exists():
            return render(self.request, self.template_name, {
                'alert': error.USER_EMAIL_DUPLICATED
            })

        user = TBLUser()
        user.email = email
        user.username = username
        user.balance = 20
        user.set_password(password)

        setting = list(TBLSetting.objects.all().values())
        if len(setting) > 0:
            setting = setting[0]
            user.permission = json.dumps({
                'max_active_bridges': setting['max_active_bridges'],
                'rate_limit_per_url': setting['rate_limit_per_url'],
                'allowed_frequency': setting['allowed_frequency'],
                'allowed_file_flush': setting['allowed_file_flush'],
                'available_bridges': setting['available_bridges']
            })

        user.save()

        transaction = TBLTransaction()
        transaction.user_id = user.id
        transaction.amount = 20
        transaction.balance = 20
        transaction.description = 'Add Credit'
        transaction.notes = 'Free Credit'
        transaction.save()

        django_login(self.request, user)
        return redirect('/data_bridges')


class PasswordResetView(TemplateView):
    template_name = 'auth/password_reset.html'

    def post(self, *args, **kwargs):
        email = self.request.POST['email']
        if TBLUser.objects.filter(email=email).exists():
            user = TBLUser.objects.get(email=email)
            reset_link = common.generate_random_string(32)
            user.reset_link = reset_link
            user.save()

            reset_url = f'{admin_config.HOST_URL}auth/change_password/{reset_link}'
            content = f'Please use below link to reset your password.\n{reset_url}'

            status, text = mail.send_email(self.request, email, 'RESET_LINK', content)
        else:
            status, text = True, ''

        if status:
            response = {
                'success': error.RESET_LINK_SENT
            }
        else:
            response = {
                'alert': error.UNKNOWN_PROBLEM
            }
            if admin_config.TRACE_MODE:
                print(text)

        return render(self.request, self.template_name, response)


class ChangePasswordView(TemplateView):
    template_name = 'auth/change_password.html'

    def dispatch(self, request, *args, **kwargs):
        reset_link = kwargs['param1']
        if not TBLUser.objects.filter(reset_link=reset_link).exists():
            return redirect('/404_page')
        else:
            return super(ChangePasswordView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ChangePasswordView, self).get_context_data(*args, **kwargs)
        context['reset_link'] = kwargs['param1']

        return context

    def post(self, *args, **kwargs):
        password = self.request.POST['password']
        reset_link = self.request.POST['reset_link']
        if not reset_link or not TBLUser.objects.filter(reset_link=reset_link).exists():
            response = {
                'alert': error.UNKNOWN_PROBLEM
            }
            return render(self.request, self.template_name, response)
        else:
            user = TBLUser.objects.get(reset_link=reset_link)
            user.set_password(password)
            user.reset_link = ''
            user.save()
            django_login(self.request, user)
            return redirect('/data_bridges')


def super_login(request):
    params = request.POST
    user_id = params['user_id']
    user = TBLUser.objects.get(id=user_id)
    django_login(request, user)

    return HttpResponse('success')
