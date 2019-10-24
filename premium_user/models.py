from django.db import models
from login.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.fields import ArrayField
from datetime import datetime

# Create your models here.
class PremiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.SmallIntegerField()
    phone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        return self.email

class AddGroup(models.Model):
    admin = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    gtype = models.SmallIntegerField()
    price = models.FloatField()
    members = ArrayField(models.CharField(max_length=50), null = True)
    
    def __str__(self):
        return self.name

class Group(models.Model):
    admin = models.CharField(max_length=30)
    group_list = ArrayField(models.CharField(max_length=50), null = True)


class GroupRequest(models.Model):
    admin = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    status = models.SmallIntegerField()
    members = ArrayField(models.CharField(max_length=50, null = True)) 
    
    def __str__(self):
        return self.admin
    
class GroupPlan(models.Model):
    customer = models.CharField(max_length=30)
    recharge_on = models.DateTimeField()
    plantype = models.CharField(max_length=30)
    noofgroup = models.FloatField()

    def __str__(self):
        return self.customer

class Message(models.Model):
    sender = models.CharField(max_length=40)
    receiver = models.CharField(max_length=40)
    messages = ArrayField(models.CharField(max_length=1000, null = True))
    timestamp = ArrayField(models.DateTimeField())
    
    def __str__(self):
        return self.sender

