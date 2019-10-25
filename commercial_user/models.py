from django.db import models
from login.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.fields import ArrayField
from datetime import datetime

# Create your models here.
class CommercialUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.SmallIntegerField()
    phone = PhoneNumberField(blank=True)
    email = models.EmailField()
    subscription_paid = models.BooleanField(default=False)
    statusofrequest = models.SmallIntegerField(default=1) #value 1 means no request sent, 4 means request sent but pending
    #, 2 means request accepted and 3 means request declined
    #value may change from 1 to 2 or 1 to 3 but cannot change once value is 2 or 3
    pan = models.IntegerField(default=0) #0 means Pan value yet not filled(Valid PAN is 8-digit number b/w 10000000-99999999)

    def __str__(self):
        return self.email
    
class Pages(models.Model):
    username = models.CharField(max_length=30)
    title = ArrayField(models.CharField(max_length=50, null=True))
    description = ArrayField(models.CharField(max_length=250, null=True))
    page_link = ArrayField(models.CharField(max_length=100, null=True))

    def __str__(self):
        return self.username

