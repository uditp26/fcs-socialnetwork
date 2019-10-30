from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, 'Superuser'),
        (1, 'Casual User'),
        (2, 'Premium User'),
        (3, 'Commercial User'),
    )

    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=0)

class FailedLogin(models.Model):
    username = models.CharField(max_length=30)
    count = models.PositiveSmallIntegerField()
    last_login = models.DecimalField(decimal_places=2, max_digits=20)
    next_login = models.DecimalField(decimal_places=2, max_digits=20)

