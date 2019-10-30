from django.contrib import admin
from .models import PremiumUser, AddGroup, Group, GroupRequest, GroupPlan, Message, Encryption

admin.site.register(PremiumUser)
admin.site.register(AddGroup)
admin.site.register(Group)
admin.site.register(GroupRequest)
admin.site.register(GroupPlan)
admin.site.register(Message)
admin.site.register(Encryption)
