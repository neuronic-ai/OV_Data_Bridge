from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *
from django.views.generic import RedirectView

urlpatterns = [
    path('', login_required(HomeView.as_view()), name=''),
    path('dashboard', login_required(DashboardView.as_view()), name='dashboard'),

    path('data_bridges', DataBridgesView.as_view(), name='data_bridges'),
    path('save_bridge', save_bridge, name='save_bridge'),
    path('report_bridge', report_bridge, name='report_bridge'),
    path('power_bridge', power_bridge, name='power_bridge'),
    path('delete_bridge', delete_bridge, name='delete_bridge'),

    path('profile', ProfileView.as_view(), name='profile'),
    path('change_password', ChangePasswordView.as_view(), name='change_password'),

    path('user', UserView.as_view(), name='user'),
    path('edit_user/<int:param1>', EditUserView.as_view(), name='edit_user'),

    path('404_page', Page404View.as_view(), name='404_page'),
]
