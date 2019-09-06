from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    url(r'^$', views.LoginFormView.as_view(), name='login'),
    url(r'register/$', views.RegistrationFormView.as_view(), name='register'),
]