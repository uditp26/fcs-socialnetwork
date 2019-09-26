from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'casual_user'

urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name='homepage'),
    url(r'^myprofile$', views.ProfileView.as_view(), name='myprofile'),
]