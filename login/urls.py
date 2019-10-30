from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    url(r'^$', views.LoginFormView.as_view(), name='login'),
    url(r'register/$', views.RegistrationFormView.as_view(), name='register'),
    url(r'regsuccess/$', views.RegistrationSuccessView.as_view(), name='successful_reg'),
    url(r'password_reset/$', views.PasswordResetView.as_view(), name='password_reset'),
    url(r'password_reset_done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'password_reset_complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'logout/$', views.LogoutView.as_view(), name='logout'),
]

