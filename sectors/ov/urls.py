from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *
from django.views.generic import RedirectView

urlpatterns = [
    path('', login_required(HomeView.as_view()), name=''),
    path('dashboard', login_required(DashboardView.as_view()), name='dashboard'),

    path('data_bridges', login_required(DataBridgesView.as_view()), name='data_bridges'),
    path('save_bridge', login_required(save_bridge), name='save_bridge'),
    path('report_bridge', login_required(report_bridge), name='report_bridge'),
    path('power_bridge', login_required(power_bridge), name='power_bridge'),
    path('delete_bridge', login_required(delete_bridge), name='delete_bridge'),

    path('profile', login_required(ProfileView.as_view()), name='profile'),
    path('change_password', login_required(ChangePasswordView.as_view()), name='change_password'),

    path('user', login_required(UserView.as_view()), name='user'),
    path('edit_user/<int:param1>', login_required(EditUserView.as_view()), name='edit_user'),
    path('save_user', login_required(save_user), name='save_user'),
    path('delete_user', login_required(delete_user), name='delete_user'),

    path('setting', login_required(SettingView.as_view()), name='setting'),
    path('test_smtp', login_required(test_smtp), name='test_smtp'),
    path('save_setting', login_required(save_setting), name='save_setting'),

    path('404_page', Page404View.as_view(), name='404_page'),
]
