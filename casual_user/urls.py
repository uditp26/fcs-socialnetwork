from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'casual_user'

urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name='homepage'),
    url(r'myprofile/$', views.ProfileView.as_view(), name='myprofile'),
    url(r'editprofile/$', views.EditProfileFormView.as_view(), name='editprofile'),
    url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
    path('listuser/<slug:casualuser>/', views.CasualUserDetailView.as_view(), name='casualuserdetail'),

    url(r'friendrequest/$', views.FriendRequestView.as_view(), name='friendrequest'),
    url(r'friend/$', views.FriendView.as_view(), name='friend'),

    #group
    url(r'listgroup/$', views.ListGroupView.as_view(), name='listgroup'),
    url(r'yourjoinedgroup/$', views.JoinedGroupView.as_view(), name='yourjoinedgroup'),
     
    #wallet
    url(r'mywallet/$', views.WalletView.as_view(), name="wallet"),
    url(r'mywallet/addmoney/$', views.AddMoneyFormView.as_view(), name="addmoney"),
    url(r'mywallet/sendmoney/$', views.SendMoneyFormView.as_view(), name="sendmoney"),
    url(r'mywallet/requestmoney/$', views.RequestMoneyFormView.as_view(), name="requestmoney"),
    url(r'mywallet/pendingrequests/$', views.PendingRequestsView.as_view(), name="pendingrequests"),

]