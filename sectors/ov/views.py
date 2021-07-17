from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.http import HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from sectors.common import error
from sectors.common import admin_config

from db.models import (
    TBLBridge,
)


class HomeView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        return redirect('/data_bridges')


class DashboardView(TemplateView):
    template_name = 'ov/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        context['page_name'] = 'dashboard'
        context['username'] = self.request.user.username

        return context


class DataBridgesView(TemplateView):
    template_name = 'ov/data_bridges.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DataBridgesView, self).get_context_data(*args, **kwargs)
        context['page_name'] = 'data_bridges'
        context['username'] = self.request.user.username
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

    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     'wsconnection1',
    #     {
    #         'type': 'notify',
    #         'cooker': 'jong',
    #         'owner': 'ho',
    #         'menu': 'jogaebap',
    #         'when': 'tomorrow',
    #         'where': '1st floor',
    #     }
    # )

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
            return JsonResponse({
                'status_code': 200,
                'text': error.SUCCESS,
                'cache': admin_config.BRIDGE_HANDLE.get_bridge_cache(bridge_id)
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
        context['page_name'] = 'profile'
        context['username'] = self.request.user.username
        context['email'] = self.request.user.email

        return context


class ChangePasswordView(TemplateView):
    template_name = 'ov/change_password.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ChangePasswordView, self).get_context_data(*args, **kwargs)
        context['page_name'] = 'profile'
        context['username'] = self.request.user.username

        return context
