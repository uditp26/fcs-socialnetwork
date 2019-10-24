from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'commercial_user'

urlpatterns = [
    url(r'^$', views.MainHomepageView.as_view(), name='homepage'),
    url(r'payment/$', views.PaymentView.as_view(), name='payment'),
    url(r'myprofile/$', views.ProfileView.as_view(), name='myprofile'),
    url(r'editprofile/$', views.EditProfileFormView.as_view(), name='editprofile'),   
    url(r'addgroup/$', views.AddGroupFormView.as_view(), name='addgroup'),
    url(r'listrequest/$', views.ListRequestView.as_view(), name='listrequest'),
    url(r'createpage/$', views.CreatePagesFormView.as_view(), name='createpage'),
    url(r'mypages/$', views.MyPagesListView.as_view(), name='mypages'),
    path('mypages/<slug:username>/<slug:url>/', views.ViewMyPageView.as_view(), name='viewpage'),
    
    #to be added(all below views)
    
    #url(r'listuser/$', views.ListUserView.as_view(), name='listuser'),
    #url(r'friend/$', views.FriendView.as_view(), name='friend'),

#    url(r'listgroup/$', views.ListGroupView.as_view(), name='listgroup'),
    url(r'verify/$', views.VerifyPanFormView.as_view(), name='verifypan'),
    url(r'denied/$', views.DeniedAccessView.as_view(), name='denied'),
    url(r'mywallet/$', views.WalletView.as_view(), name="wallet"),
    url(r'mywallet/addmoney/$', views.AddMoneyFormView.as_view(), name="addmoney"),
    url(r'mywallet/sendmoney/$', views.SendMoneyFormView.as_view(), name="sendmoney"),
    url(r'mywallet/requestmoney/$', views.RequestMoneyFormView.as_view(), name="requestmoney"),
    url(r'mywallet/addmoneynew/$', views.AddMoneyFormToSubscribeView.as_view(), name="addmoneytosubscribe"),
    
    #url(r'mywallet/pendingrequests/$', views.PendingRequestsView.as_view(), name="pendingrequests"),
    
]