from django.contrib import admin
from .models import User, FailedLogin

admin.site.register(User)
admin.site.register(FailedLogin)

