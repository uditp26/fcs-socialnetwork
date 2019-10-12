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

class Post(models.Model):
    username = models.CharField(max_length=30)
    private_posts = ArrayField(models.CharField(max_length=500))
    friends_posts = ArrayField(models.CharField(max_length=500))
    prv_timestamp = ArrayField(models.DateTimeField())
    frnd_timestamp = ArrayField(models.DateTimeField())

    def __str__(self):
        return self.username

class Friend(models.Model):
    username = models.CharField(max_length = 30)
    friend_list = ArrayField(models.CharField(max_length=50, blank=True))
    
    def __str__(self):
        return self.username
        

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
