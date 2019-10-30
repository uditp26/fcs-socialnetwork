from django.contrib import admin
from .models import CasualUser, Post, Friend, FriendRequest, Wallet, Request, Transaction, Timeline

admin.site.register(CasualUser)
admin.site.register(Post)
admin.site.register(Friend)
admin.site.register(FriendRequest)
admin.site.register(Wallet)
admin.site.register(Request)
admin.site.register(Transaction)
admin.site.register(Timeline)
