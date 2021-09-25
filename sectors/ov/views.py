from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate
from django.http import JsonResponse
from operator import itemgetter
import _thread as thread
import json
import os

from sectors.common import admin_config, error, mail
from sectors.module import common

from db.models import (
    TBLBridge,
    TBLLog,
    TBLUser,
    TBLSetting,
    TBLTransaction,
)


def put_base_info(request, context, page_name):
    context['page_name'] = page_name
    context['username'] = request.user.username
    context['email'] = request.user.email
    context['is_superuser'] = request.user.is_superuser

    return context


class HomeView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        return redirect('/data_bridges')


class DashboardView(TemplateView):
    template_name = 'ov/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'dashboard')

        return context


class DataBridgesView(TemplateView):
    template_name = 'ov/data_bridges.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DataBridgesView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'data_bridges')
        context['permission'] = json.loads(self.request.user.permission)
        context['bridges_info'] = list(TBLBridge.objects.filter(user_id=self.request.user.id).values())
        for bi in context['bridges_info']:
            bi['description'] = admin_config.get_bridge_by_type(bi['type'])['description']
            bi['date_created'] = bi['date_created'].strftime('%B %d, %Y')
            bi['date_updated'] = bi['date_updated'].strftime('%B %d, %Y')

            if bi['format'] is None:
                bi['format'] = ''

            bi['is_active'] = int(bi['is_active'])

            del bi['user_id']

        context['frequency'] = admin_config.FREQUENCY
        context['flush'] = admin_config.FLUSH
        context['file_format'] = admin_config.FILE_FORMAT

        return context


def save_bridge(request):
    params = request.POST

    try:
        if int(params['id']) == 0:  # new bridge
            bridge = TBLBridge()
        else:
            bridge = TBLBridge.objects.get(id=int(params['id']))

        bridge_type = int(params['type'])

        if bridge_type in [5, 6, 7]:
            resp_data, status_code = common.check_validity_remote_file(request, params['src_address'])
            if status_code >= 300:
                return JsonResponse({
                    'status_code': status_code,
                    'text': resp_data
                })

        bridge.user = request.user
        bridge.name = params['name']
        bridge.type = bridge_type
        bridge.src_address = params['src_address']
        bridge.dst_address = params['dst_address']
        if 'format' in params:
            bridge.format = params['format']
        if 'frequency' in params:
            bridge.frequency = int(params['frequency'])
        if 'flush' in params:
            bridge.flush = int(params['flush'])
        if 'file_format' in params:
            bridge.file_format = params['file_format']

        bridge_qty = TBLBridge.objects.filter(user=request.user, is_active=True).count()
        if bridge.is_active:
            bridge_qty -= 1

        max_active_bridges = json.loads(request.user.permission)['max_active_bridges']
        if not max_active_bridges > bridge_qty:
            bridge.is_active = False

        bridge.save()

        if bridge.is_active:
            admin_config.BRIDGE_HANDLE.restart_bridge_by_id(bridge.id)

        return JsonResponse({
            'status_code': 200,
            'text': error.SUCCESS
        })
    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def report_bridge(request):
    params = request.POST
    try:
        bridge_id = int(params['id'])
        bridge = TBLBridge.objects.get(id=bridge_id)
        if bridge.user_id == request.user.id:
            logs_info = list(TBLLog.objects.filter(bridge_id=bridge_id).values())

            for log in logs_info:
                log['date_from'] = log['date_from'].strftime('%m/%d, %H:%M:%S')
                log['date_to'] = log['date_to'].strftime('%m/%d, %H:%M:%S')
                log['url'] = f"{admin_config.BRIDGE_LOG_ZIP_DOWNLOAD}/{log['filename']}"

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS,
                'cache': admin_config.BRIDGE_HANDLE.get_bridge_cache(bridge_id)[::-1],
                'logs_info': logs_info[::-1]
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def power_bridge(request):
    params = request.POST

    try:
        bridge_id = int(params['id'])
        is_active = int(params['is_active'])
        bridge = TBLBridge.objects.get(id=bridge_id)
        if bridge.user_id == request.user.id:
            if is_active:
                bridge.is_active = False
                admin_config.BRIDGE_HANDLE.stop_bridge_by_id(bridge_id)
            else:
                # check available_bridges
                available_bridges = json.loads(request.user.permission)['available_bridges']
                for i in range(1, 5):
                    if not available_bridges[f'ab{i}'] and bridge.type == i:
                        return JsonResponse({
                            'status_code': 401,
                            'text': error.BRIDGE_TYPE_NOT_EXCEED
                        })

                # check max_active_bridges
                bridge_qty = TBLBridge.objects.filter(user_id=bridge.user_id, is_active=True).count()
                max_active_bridges = json.loads(request.user.permission)['max_active_bridges']
                if max_active_bridges > bridge_qty:
                    bridge.is_active = True
                    admin_config.BRIDGE_HANDLE.start_bridge_by_id(bridge_id)
                else:
                    return JsonResponse({
                        'status_code': 401,
                        'text': error.MAX_ACTIVE_BRIDGES_EXCEED
                    })

            bridge.save()

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })

        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def delete_bridge_log(request, bridge_id):
    if admin_config.DELETE_LOG_AFTER_BRIDGE_DELETED:
        try:
            os.remove(f'{admin_config.BRIDGE_LOG_PATH}/{admin_config.BRIDGE_LOG_PREFIX}_{bridge_id}.log')
        except:
            pass


def delete_bridge(request):
    params = request.POST

    try:
        bridge_id = int(params['id'])
        bridge = TBLBridge.objects.get(id=bridge_id)
        if bridge.user_id == request.user.id:
            bridge.delete()
            admin_config.BRIDGE_HANDLE.remove_bridge_by_id(bridge_id)
            delete_bridge_log(request, bridge_id)

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


class ProfileView(TemplateView):
    template_name = 'ov/profile.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ProfileView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'profile')

        return context


class ChangePasswordView(TemplateView):
    template_name = 'ov/change_password.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ChangePasswordView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'profile')

        if 'change_password_msg' in self.request.session:
            context['msg'] = self.request.session['change_password_msg']
            del self.request.session['change_password_msg']

        return context

    def post(self, *args, **kwargs):
        old_password = self.request.POST['old_password']
        password = self.request.POST['password']

        user = authenticate(username=self.request.user.username, password=old_password)
        if user:
            user = TBLUser.objects.get(id=self.request.user.id)
            user.set_password(password)
            user.save()

            thread.start_new_thread(mail.send_email, (self.request, self.request.user.email, 'PASSWORD_CHANGED'))
        else:
            self.request.session['change_password_msg'] = error.RESET_FAIL
            return redirect('/change_password')

        return redirect('/profile')


class UserView(TemplateView):
    template_name = 'ov/user.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(UserView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(*args, **kwargs)
        put_base_info(self.request, context, 'user')
        bridges_status = {
            'active_wss': 0,
            'active_wh': 0,
            'active_api': 0,
            'active_file': 0,
            'active_total': 0
        }

        bridges_info = TBLBridge.objects.all()
        users_info = list(TBLUser.objects.all().values('id', 'is_superuser', 'username', 'email', 'date_joined', 'balance', 'spent', 'permission'))
        u_id = 1
        for ui in users_info:
            ui['uid'] = u_id
            ui['total'] = 0
            ui['active'] = 0
            ui['inactive'] = 0

            for bi in bridges_info:
                if bi.user_id == ui['id']:
                    if bi.is_active:
                        if bi.type in [2, 6]:
                            bridges_status['active_wss'] += 1
                        elif bi.type in [1, 3, 5]:
                            bridges_status['active_wh'] += 1
                        elif bi.type in [4, 7]:
                            bridges_status['active_api'] += 1
                        elif bi.type in [8, 9, 10]:
                            bridges_status['active_file'] += 1

                        ui['active'] += 1
                        bridges_status['active_total'] += 1
                    else:
                        ui['inactive'] += 1

                    ui['total'] += 1

            u_id += 1

        context['bridges_status'] = bridges_status
        context['users_info'] = users_info

        return context


class EditUserGeneralView(TemplateView):
    template_name = 'ov/edit_user.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(EditUserGeneralView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EditUserGeneralView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'user')

        user_id = kwargs['param1']

        user = TBLUser.objects.get(id=user_id)
        context['edit_user_id'] = user.id
        context['edit_username'] = user.username
        context['edit_email'] = user.email
        context['edit_permission'] = json.loads(user.permission)
        context['edit_permission']['allowed_frequency'] = json.dumps(context['edit_permission']['allowed_frequency'])
        context['edit_permission']['allowed_file_flush'] = json.dumps(context['edit_permission']['allowed_file_flush'])
        context['edit_permission']['available_bridges'] = json.dumps(context['edit_permission']['available_bridges'])

        bridges_info = TBLBridge.objects.filter(user_id=user_id)

        context['active_wss'] = 0
        context['active_wh'] = 0
        context['active_api'] = 0
        context['active_file'] = 0
        context['active_total'] = 0

        for bi in bridges_info:
            if bi.is_active:
                if bi.type in [2, 6]:
                    context['active_wss'] += 1
                elif bi.type in [1, 3, 5]:
                    context['active_wh'] += 1
                elif bi.type in [4, 7]:
                    context['active_api'] += 1
                elif bi.type in [8, 9, 10]:
                    context['active_file'] += 1

                context['active_total'] += 1

        return context


class EditUserAccountView(TemplateView):
    template_name = 'ov/edit_user_account.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(EditUserAccountView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EditUserAccountView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'user')

        user_id = kwargs['param1']

        user = TBLUser.objects.get(id=user_id)
        context['edit_user_id'] = user.id
        context['edit_balance'] = user.balance

        # get transaction info
        transactions_info = list(TBLTransaction.objects.filter(user_id=user_id).values())

        sp = 1
        for transaction in transactions_info:
            transaction['id'] = sp
            transaction['date_created'] = transaction['date_created'].strftime('%m/%d/%Y, %H:%M:%S')
            sp += 1

        context['transactions_info'] = transactions_info

        # get bridge info
        bridges_info = TBLBridge.objects.filter(user_id=user_id)

        context['active_wss'] = 0
        context['active_wh'] = 0
        context['active_api'] = 0
        context['active_file'] = 0
        context['active_total'] = 0

        for bi in bridges_info:
            if bi.is_active:
                if bi.type in [2, 6]:
                    context['active_wss'] += 1
                elif bi.type in [1, 3, 5]:
                    context['active_wh'] += 1
                elif bi.type in [4, 7]:
                    context['active_api'] += 1
                elif bi.type in [8, 9, 10]:
                    context['active_file'] += 1

                context['active_total'] += 1

        return context


class ResetPasswordView(TemplateView):
    template_name = 'ov/reset_password.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(ResetPasswordView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'user')

        user_id = kwargs['param1']
        self.request.session['reset_password_user_id'] = user_id

        return context

    def post(self, *args, **kwargs):
        password = self.request.POST['password']
        user_id = self.request.session['reset_password_user_id']
        del self.request.session['reset_password_user_id']

        user = TBLUser.objects.get(id=user_id)
        user.set_password(password)
        user.save()

        thread.start_new_thread(mail.send_email, (self.request, self.request.user.email, 'PASSWORD_CHANGED'))

        return redirect('/user')


def save_user(request):
    params = request.POST

    try:
        user_id = int(params['user_id'])

        if request.user.is_superuser:
            user = TBLUser.objects.get(id=user_id)
            allowed_frequency = json.loads(params['allowed_frequency'])
            allowed_file_flush = json.loads(params['allowed_file_flush'])
            available_bridges = json.loads(params['available_bridges'])
            user.permission = json.dumps({
                'max_active_bridges': int(params['max_active_bridges']),
                'rate_limit_per_url': int(params['rate_limit_per_url']),
                'allowed_frequency': allowed_frequency,
                'allowed_file_flush': allowed_file_flush,
                'available_bridges': available_bridges
            })
            user.save()

            bridges_obj = TBLBridge.objects.filter(user_id=user_id, is_active=True)
            bridges_info = list(bridges_obj.values('id', 'type', 'date_created'))

            # check available_bridges
            for bridge_info in bridges_info:
                for i in range(1, 5):
                    if not available_bridges[f'ab{i}'] and bridge_info['type'] == i:
                        bridge = TBLBridge.objects.get(id=bridge_info['id'])
                        bridge.is_active = False
                        bridge.save()

                        admin_config.BRIDGE_HANDLE.stop_bridge_by_id(bridge_info['id'])
                        bridges_info.remove(bridge_info)

            # check max_active_bridges
            if len(bridges_info) > int(params['max_active_bridges']):
                sorted(bridges_info, key=itemgetter('date_created'))
                sp = 0
                for bridge_info in bridges_info:
                    if sp >= int(params['max_active_bridges']):
                        bridge = TBLBridge.objects.get(id=bridge_info['id'])
                        bridge.is_active = False
                        bridge.save()

                        admin_config.BRIDGE_HANDLE.stop_bridge_by_id(bridge_info['id'])

                    sp += 1

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def update_user_balance(request):
    params = request.POST

    try:
        user_id = int(params['user_id'])

        if request.user.is_superuser:
            user = TBLUser.objects.get(id=user_id)
            user.balance = round(user.balance + float(params['amount']), admin_config.ROUND_DIGIT)
            user.save()

            if user.balance > 0:
                TBLBridge.objects.filter(user_id=user_id).update(is_status=0)

            transaction = TBLTransaction()
            transaction.user_id = user_id
            transaction.amount = round(float(params['amount']), admin_config.ROUND_DIGIT)
            transaction.balance = user.balance
            transaction.description = 'Add Credit'
            transaction.notes = params['notes']
            transaction.save()

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def delete_user(request):
    params = request.POST

    try:
        user_id = int(params['user_id'])

        if request.user.is_superuser:
            bridges_info = list(TBLBridge.objects.filter(user_id=user_id).values('id'))
            for bi in bridges_info:
                admin_config.BRIDGE_HANDLE.remove_bridge_by_id(bi['id'])
                delete_bridge_log(request, bi['id'])

            user = TBLUser.objects.get(id=user_id)
            user.delete()

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


class SettingServerView(TemplateView):
    template_name = 'ov/setting.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(SettingServerView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(SettingServerView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'setting')

        setting = list(TBLSetting.objects.all().values())

        if len(setting) == 0:
            setting_data = {
                'server_setting': json.dumps({
                    'server_name': '',
                    'priv_key_directory': '',
                    'cert_directory': '',
                    'privacy_link': '',
                    'user_link': ''
                }),
                'max_active_bridges': admin_config.DEFAULT_MAX_ACTIVE_BRIDGES,
                'rate_limit_per_url': admin_config.DEFAULT_RATE_LIMIT_PER_URL,
                'allowed_frequency': json.dumps(admin_config.DEFAULT_ALLOWED_FREQUENCY),
                'allowed_file_flush': json.dumps(admin_config.DEFAULT_ALLOWED_FILE_FLUSH),
                'available_bridges': json.dumps(admin_config.DEFAULT_AVAILABLE_BRIDGE)
            }
        else:
            setting = setting[0]
            setting_data = {
                'server_setting': json.dumps(setting['server_setting']),
                'max_active_bridges': setting['max_active_bridges'],
                'rate_limit_per_url': setting['rate_limit_per_url'],
                'allowed_frequency': json.dumps(setting['allowed_frequency']),
                'allowed_file_flush': json.dumps(setting['allowed_file_flush']),
                'available_bridges': json.dumps(setting['available_bridges'])
            }

        context['setting_data'] = setting_data

        return context


class SettingPriceView(TemplateView):
    template_name = 'ov/setting_price.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(SettingPriceView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(SettingPriceView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'setting')

        setting = list(TBLSetting.objects.all().values())

        if len(setting) == 0:
            bridge_price = admin_config.BRIDGE_PRICE
            frequency_price = admin_config.FREQUENCY_PRICE
            disable_pricing = admin_config.DISABLE_PRICING
        else:
            setting = setting[0]
            disable_pricing = setting['price_setting']['disable_pricing']
            bridge_price = setting['price_setting']['bridge_price']
            frequency_price = setting['price_setting']['frequency_price']

        for bp in bridge_price:
            bp['name'] = admin_config.get_bridge_by_type(bp['type'])['reg']

        for fp in frequency_price:
            fp['name'] = admin_config.get_frequency_by_type(fp['type'])['reg']

        context['disable_pricing'] = disable_pricing
        context['bridge_price'] = bridge_price
        context['frequency_price'] = frequency_price

        return context


class SettingSMTPView(TemplateView):
    template_name = 'ov/setting_smtp.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/404_page')
        else:
            return super(SettingSMTPView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(SettingSMTPView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'setting')

        setting = list(TBLSetting.objects.all().values())

        if len(setting) == 0:
            setting_data = {
                'smtp_setting': json.dumps({
                    'smtp_server_name': '',
                    'smtp_port': '',
                    'smtp_authentication': True,
                    'smtp_enable_starttls': True,
                    'smtp_username': '',
                    'smtp_password': ''
                })
            }
        else:
            setting = setting[0]
            setting_data = {
                'smtp_setting': json.dumps(setting['smtp_setting'])
            }

        context['setting_data'] = setting_data

        return context


def test_smtp(request):
    params = request.POST

    try:
        if request.user.is_superuser:

            smtp_setting = json.loads(params['smtp_setting'])
            status, text = mail.test_smtp(request, smtp_setting)
            if status:
                return JsonResponse({
                    'status_code': 200,
                    'text': error.SUCCESS
                })
            else:
                return JsonResponse({
                    'status_code': 500,
                    'text': text
                })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


def save_setting(request):
    params = request.POST

    try:
        if request.user.is_superuser:
            setting = TBLSetting.objects.all()
            if len(setting) == 0:
                setting = TBLSetting()
                setting.server_setting = {
                    'server_name': '',
                    'priv_key_directory': '',
                    'cert_directory': '',
                    'privacy_link': '',
                    'user_link': ''
                }
                setting.max_active_bridges = admin_config.DEFAULT_MAX_ACTIVE_BRIDGES
                setting.rate_limit_per_url = admin_config.DEFAULT_RATE_LIMIT_PER_URL
                setting.allowed_frequency = admin_config.DEFAULT_ALLOWED_FREQUENCY
                setting.allowed_file_flush = admin_config.DEFAULT_ALLOWED_FILE_FLUSH
                setting.available_bridges = admin_config.DEFAULT_AVAILABLE_BRIDGE
                setting.price_setting = {
                    'disable_pricing': admin_config.DISABLE_PRICING,
                    'bridge_price': admin_config.BRIDGE_PRICE,
                    'frequency_price': admin_config.FREQUENCY_PRICE
                }
                setting.smtp_setting = {
                    'smtp_server_name': '',
                    'smtp_port': '',
                    'smtp_authentication': True,
                    'smtp_enable_starttls': True,
                    'smtp_username': '',
                    'smtp_password': ''
                }
            else:
                setting = setting[0]

            if 'server_setting' in params:
                setting.server_setting = json.loads(params['server_setting'])
            if 'max_active_bridges' in params:
                setting.max_active_bridges = int(params['max_active_bridges'])
            if 'rate_limit_per_url' in params:
                setting.rate_limit_per_url = int(params['rate_limit_per_url'])
            if 'allowed_frequency' in params:
                setting.allowed_frequency = json.loads(params['allowed_frequency'])
            if 'allowed_file_flush' in params:
                setting.allowed_file_flush = json.loads(params['allowed_file_flush'])
            if 'available_bridges' in params:
                setting.available_bridges = json.loads(params['available_bridges'])
            if 'price_setting' in params:
                setting.price_setting = json.loads(params['price_setting'])
            if 'smtp_setting' in params:
                setting.smtp_setting = json.loads(params['smtp_setting'])

            setting.save()

            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS
            })
        else:
            return JsonResponse({
                'status_code': 401,
                'text': error.PERMISSION_NOT_ALLOWED
            })

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'text': str(e)
        })


class Page404View(TemplateView):
    template_name = 'ov/404.html'

    def dispatch(self, request, *args, **kwargs):
        return super(Page404View, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(Page404View, self).get_context_data(*args, **kwargs)
        return context
