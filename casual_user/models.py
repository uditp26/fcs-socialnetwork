from django.db import models
from login.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.fields import ArrayField
from datetime import datetime

class CasualUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.SmallIntegerField()
    phone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        return self.email
    
    # def name_to_url(self):
    #     name = str(self.email).split('@')[0]
    #     return name
    # def name_to_url(self):
    #     return self.user

class Post(models.Model):
    username = models.CharField(max_length=30)
    friends_posts = ArrayField(models.CharField(max_length=500))
    public_posts = ArrayField(models.CharField(max_length=500))
    frnd_timestamp = ArrayField(models.DateTimeField())
    pblc_timestamp = ArrayField(models.DateTimeField())

    def __str__(self):
        return self.username

class Friend(models.Model):
    username = models.CharField(max_length = 30)
    friend_list = ArrayField(models.CharField(max_length=50, blank=True))
    
    def __str__(self):
        return self.username

class FriendRequest(models.Model):
    requestto = models.CharField(max_length=30)
    requestfrom = ArrayField(models.CharField(max_length=50, null = True)) 
    
    def __str__(self):
        return self.requestto

class Wallet(models.Model):
    username = models.CharField(max_length=30)
    user_type = models.SmallIntegerField()
    amount = models.FloatField()
    transactions_left = models.PositiveIntegerField()

    def __str__(self):
        return self.username

class Request(models.Model):
    request_id = models.CharField(max_length=15)
    sender = models.CharField(max_length=30)
    receiver = models.CharField(max_length=30)
    amount = models.FloatField()
    status = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.sender

class Transaction(models.Model):
    sender = models.CharField(max_length=30)
    receiver = models.CharField(max_length=30)
    amount = models.FloatField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return self.sender

class Timeline(models.Model):
    username = models.CharField(max_length=30)
    level = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.username


