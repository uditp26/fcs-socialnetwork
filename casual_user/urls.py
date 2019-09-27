from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'casual_user'

urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name='homepage'),
    url(r'^myprofile$', views.ProfileView.as_view(), name='myprofile'),
    # url(r'^findfriend/$', views.findfriend, name = 'findfriend'),
     url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
     url(r'friend/$', views.FriendView.as_view(), name='friend'),
    #  url(r'findbtn/$', views.findbutton, name='findbtn'),
     
]