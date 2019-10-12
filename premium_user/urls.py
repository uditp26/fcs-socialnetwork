from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'premium_user'

urlpatterns = [
    url(r'^myprofile$', views.ProfileView.as_view(), name='myprofile'),     
    url(r'addgroup/$', views.AddGroupFormView.as_view(), name='addgroup'),
    url(r'listrequest/$', views.ListRequestView.as_view(), name='listrequest'),
]