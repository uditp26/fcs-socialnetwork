from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'commercial_user'

urlpatterns = [
    url(r'^$', views.MainHomepageView.as_view(), name='homepage'),
    url(r'myprofile/$', views.ProfileView.as_view(), name='myprofile'),
    url(r'editprofile/$', views.EditProfileFormView.as_view(), name='editprofile'),   
    url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
    path('listuser/<slug:username>/', views.UserProfileView.as_view(), name='userprofile'),

    url(r'payment/$', views.PaymentView.as_view(), name='payment'),
    url(r'addgroup/$', views.AddGroupFormView.as_view(), name='addgroup'),
    url(r'listrequest/$', views.ListRequestView.as_view(), name='listrequest'),

    # pages
    url(r'createpage/$', views.CreatePagesFormView.as_view(), name='createpage'),
    url(r'mypages/$', views.MyPagesListView.as_view(), name='mypages'),
    path('mypages/<slug:username>/<slug:url>/', views.ViewMyPageView.as_view(), name='viewpage'),

    # friend
    url(r'friendrequest/$', views.FriendRequestView.as_view(), name='friendrequest'),
    url(r'friend/$', views.FriendView.as_view(), name='friend'),

    #group
    url(r'addgroup/$', views.AddGroupFormView.as_view(), name='addgroup'),
    url(r'listgroup/$', views.ListGroupView.as_view(), name='listgroup'),
    url(r'listrequest/$', views.ListRequestView.as_view(), name='listrequest'),
    url(r'groupplan/$', views.GroupPlanFormView.as_view(), name='groupplan'),
    url(r'groupdetails/$', views.GroupDetailsView.as_view(), name='groupdetails'),
    url(r'deletegroup/$', views.DeleteGroupView.as_view(), name='deletegroup'),
    url(r'yourjoinedgroup/$', views.JoinedGroupView.as_view(), name='yourjoinedgroup'),

    url(r'verify/$', views.VerifyPanFormView.as_view(), name='verifypan'),
    url(r'denied/$', views.DeniedAccessView.as_view(), name='denied'),

    #wallet
    url(r'mywallet/$', views.WalletView.as_view(), name="wallet"),
    url(r'mywallet/otpverify/$', views.OTPVerificationFormView.as_view(), name="otpverify"),
    url(r'mywallet/addmoney/$', views.AddMoneyFormView.as_view(), name="addmoney"),
    url(r'mywallet/sendmoney/$', views.SendMoneyFormView.as_view(), name="sendmoney"),
    url(r'mywallet/requestmoney/$', views.RequestMoneyFormView.as_view(), name="requestmoney"),
    url(r'mywallet/pendingrequests/$', views.PendingRequestsView.as_view(), name="pendingrequests"),
    url(r'mywallet/nofriends/$', views.NofriendsView.as_view(), name="nofriends"),
    
    url(r'subscription/$', views.AddMoneyFormToSubscribeView.as_view(), name="addmoneytosubscribe"),
    
    #post
    url(r'postcontent/$', views.PostContentView.as_view(), name='postcontent'),

    #message
    url(r'inbox/$', views.InboxView.as_view(), name="inbox"),
    url(r'chat/$', views.ChatView.as_view(), name="chat"),

    # settings
    url(r'settings/$', views.SettingsView.as_view(), name="settings"),
    
]