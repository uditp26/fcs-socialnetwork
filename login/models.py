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
