from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'casual_user'

urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name='homepage'),
    url(r'^myprofile$', views.ProfileView.as_view(), name='myprofile'),
    url(r'editprofile/$', views.EditProfileView.as_view(), name='editprofile'),
    url(r'viewprofile/$', views.ViewProfileView.as_view(), name='viewprofile'),
    url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
    url(r'friend/$', views.FriendView.as_view(), name='friend'),
     
]