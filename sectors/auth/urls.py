from django.conf.urls import include
from django.urls import path
from .views import *

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('logout', logout, name='logout'),
    path('signup', SignupView.as_view(), name='signup'),
    path('password_reset', PasswordResetView.as_view(), name='password_reset'),
]