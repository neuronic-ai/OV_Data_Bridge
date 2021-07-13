from django.shortcuts import render
from django.views.generic.base import TemplateView


class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
