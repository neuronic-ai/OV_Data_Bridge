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

    path('api_mng', login_required(ApiMngView.as_view()), name='api_mng'),
    path('save_api_key', login_required(save_api_key), name='save_api_key'),
    path('get_api_key', login_required(get_api_key), name='get_api_key'),
    path('delete_api_key', login_required(delete_api_key), name='delete_api_key'),

    path('api_ref', login_required(ApiRefView.as_view()), name='api_ref'),

    path('user', login_required(UserView.as_view()), name='user'),
    path('edit_user_general/<int:param1>', login_required(EditUserGeneralView.as_view()), name='edit_user_general'),
    path('edit_user_account/<int:param1>', login_required(EditUserAccountView.as_view()), name='edit_user_account'),
    path('reset_password/<int:param1>', login_required(ResetPasswordView.as_view()), name='reset_password'),
    path('save_user', login_required(save_user), name='save_user'),
    path('update_user_balance', login_required(update_user_balance), name='update_user_balance'),
    path('delete_user', login_required(delete_user), name='delete_user'),

    path('setting_server', login_required(SettingServerView.as_view()), name='setting_server'),
    path('setting_price', login_required(SettingPriceView.as_view()), name='setting_price'),
    path('setting_smtp', login_required(SettingSMTPView.as_view()), name='setting_smtp'),
    path('test_smtp', login_required(test_smtp), name='test_smtp'),
    path('save_setting', login_required(save_setting), name='save_setting'),

    path('404_page', Page404View.as_view(), name='404_page'),
]
