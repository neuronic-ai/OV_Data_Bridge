from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.http import JsonResponse

from sectors.common import admin_config, error

from db.models import (
    TBLBridge,
    TBLLog,
    TBLUser
)


def put_base_info(request, context, page_name):
    context['page_name'] = page_name
    context['username'] = request.user.username
    context['email'] = request.user.email
    context['is_staff'] = request.user.is_staff

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
        context['bridges_info'] = list(TBLBridge.objects.filter(user_id=self.request.user.id).values())
        for bridge_info in context['bridges_info']:
            bridge_info['description'] = admin_config.get_bridge_description(bridge_info['type'])['description']
            bridge_info['date_created'] = bridge_info['date_created'].strftime('%B %d, %Y')
            bridge_info['date_updated'] = bridge_info['date_updated'].strftime('%B %d, %Y')

            if bridge_info['format'] is None:
                bridge_info['format'] = ''

            bridge_info['is_active'] = int(bridge_info['is_active'])

            del bridge_info['user_id']

        context['frequency'] = admin_config.frequency

        return context


def save_bridge(request):
    params = request.POST

    try:
        if int(params['id']) == 0:  # new bridge
            bridge = TBLBridge()
        else:
            bridge = TBLBridge.objects.get(id=int(params['id']))

        bridge.user = request.user
        bridge.name = params['name']
        bridge.type = int(params['type'])
        bridge.src_address = params['src_address']
        bridge.dst_address = params['dst_address']
        if 'format' in params:
            bridge.format = params['format']
        if 'frequency' in params:
            bridge.frequency = int(params['frequency'])
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
                bridge.is_active = True
                admin_config.BRIDGE_HANDLE.start_bridge_by_id(bridge_id)

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


def delete_bridge(request):
    params = request.POST

    try:
        bridge_id = int(params['id'])
        bridge = TBLBridge.objects.get(id=bridge_id)
        if bridge.user_id == request.user.id:
            bridge.delete()
            admin_config.BRIDGE_HANDLE.remove_bridge_by_id(bridge_id)
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

        return context


class UserView(TemplateView):
    template_name = 'ov/user.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('/404_page')
        else:
            return super(UserView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(*args, **kwargs)
        put_base_info(self.request, context, 'user')
        bridges_status = {
            'active_api_bridges': 0,
            'active_wh_bridges': 0,
            'active_total_bridges': 0,
            'inactive_api_bridges': 0,
            'inactive_wh_bridges': 0,
            'inactive_total_bridges': 0
        }

        bridges_info = list(TBLBridge.objects.filter().values('user_id', 'type', 'is_active'))
        users_info = list(TBLUser.objects.filter().values('id', 'username', 'email', 'date_joined', 'permission'))
        u_id = 1
        for ui in users_info:
            ui['uid'] = u_id
            ui['balance'] = 0
            ui['active_api_bridges'] = 0
            ui['active_wh_bridges'] = 0
            ui['active_total_bridges'] = 0
            ui['inactive_api_bridges'] = 0
            ui['inactive_wh_bridges'] = 0
            ui['inactive_total_bridges'] = 0

            for bi in bridges_info:
                if bi['user_id'] == ui['id']:
                    if bi['is_active']:
                        if bi['type'] in [1, 2]:
                            ui['active_wh_bridges'] += 1
                            ui['active_total_bridges'] += 1
                        elif bi['type'] in [3, 4]:
                            ui['active_api_bridges'] += 1
                            ui['active_total_bridges'] += 1
                        else:
                            pass
                    else:
                        if bi['type'] in [1, 2]:
                            ui['inactive_wh_bridges'] += 1
                            ui['inactive_total_bridges'] += 1
                        elif bi['type'] in [3, 4]:
                            ui['inactive_api_bridges'] += 1
                            ui['inactive_total_bridges'] += 1
                        else:
                            pass

            ui['total_api_bridges'] = ui['active_api_bridges'] + ui['inactive_api_bridges']
            ui['total_wh_bridges'] = ui['active_wh_bridges'] + ui['inactive_wh_bridges']

            bridges_status['active_api_bridges'] += ui['active_api_bridges']
            bridges_status['active_wh_bridges'] += ui['active_wh_bridges']
            bridges_status['active_total_bridges'] += ui['active_total_bridges']
            bridges_status['inactive_api_bridges'] += ui['inactive_api_bridges']
            bridges_status['inactive_wh_bridges'] += ui['inactive_wh_bridges']
            bridges_status['inactive_total_bridges'] += ui['inactive_total_bridges']

            u_id += 1

        context['bridges_status'] = bridges_status
        context['users_info'] = users_info

        return context


class EditUserView(TemplateView):
    template_name = 'ov/edit_user.html'

    def dispatch(self, request, *args, **kwargs):
        return super(EditUserView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EditUserView, self).get_context_data(*args, **kwargs)
        context = put_base_info(self.request, context, 'user')

        user_id = kwargs['param1']
        bridges_info = list(TBLBridge.objects.filter(user_id=user_id).values('user_id', 'type', 'is_active'))

        context['api_bridges'] = 0
        context['wh_bridges'] = 0
        context['total_bridges'] = 0

        for bi in bridges_info:
            if bi['type'] in [1, 2]:
                context['wh_bridges'] += 1
            elif bi['type'] in [3, 4]:
                context['api_bridges'] += 1
            else:
                pass

            context['total_bridges'] += 1

        context['permission'] = {
            'max_active_bridges': 1,
            'rate_limit': 14
        }

        return context


class Page404View(TemplateView):
    template_name = 'ov/404.html'

    def dispatch(self, request, *args, **kwargs):
        return super(Page404View, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(Page404View, self).get_context_data(*args, **kwargs)
        return context
