from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'premium_user'

urlpatterns = [
    url(r'^$', views.HomepageView.as_view(), name='homepage'),
    url(r'myprofile/$', views.ProfileView.as_view(), name='myprofile'),
    url(r'editprofile/$', views.EditProfileFormView.as_view(), name='editprofile'),
   
    url(r'friend/$', views.FriendView.as_view(), name='friend'),
    url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
    path('listuser/<slug:username>/', views.UserProfileView.as_view(), name='userprofile'),
    url(r'friendrequest/$', views.FriendRequestView.as_view(), name='friendrequest'),
    
    url(r'addgroup/$', views.AddGroupFormView.as_view(), name='addgroup'),
    url(r'listgroup/$', views.ListGroupView.as_view(), name='listgroup'),
    url(r'listrequest/$', views.ListRequestView.as_view(), name='listrequest'),
    url(r'groupplan/$', views.GroupPlanFormView.as_view(), name='groupplan'),
    url(r'groupdetails/$', views.GroupDetailsView.as_view(), name='groupdetails'),
    url(r'deletegroup/$', views.DeleteGroupView.as_view(), name='deletegroup'),
    url(r'yourjoinedgroup/$', views.JoinedGroupView.as_view(), name='yourjoinedgroup'),
    
    url(r'mywallet/$', views.WalletView.as_view(), name="wallet"),
    url(r'mywallet/addmoney/$', views.AddMoneyFormView.as_view(), name="addmoney"),
    url(r'mywallet/sendmoney/$', views.SendMoneyFormView.as_view(), name="sendmoney"),
    url(r'mywallet/requestmoney/$', views.RequestMoneyFormView.as_view(), name="requestmoney"),
    url(r'mywallet/pendingrequests/$', views.PendingRequestsView.as_view(), name="pendingrequests"),

    url(r'inbox/$', views.InboxView.as_view(), name="inbox"),
    url(r'chat/$', views.ChatView.as_view(), name="chat"),
]