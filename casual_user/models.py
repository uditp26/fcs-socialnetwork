from django.db import models
from login.models import User
from phonenumber_field.modelfields import PhoneNumberField

#import array list 
from django.contrib.postgres.fields import ArrayField

class CasualUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.SmallIntegerField()
    phone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        return self.email


class Friend(models.Model):
    username = models.CharField(max_length = 30)
    friend_list = ArrayField(models.CharField(max_length=50, blank=True))
    
    def __str__(self):
        return self.username
