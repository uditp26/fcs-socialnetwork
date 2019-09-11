from django.db import models
from login.models import User
from phonenumber_field.modelfields import PhoneNumberField

class CasualUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.SmallIntegerField()
    phone = PhoneNumberField(blank=True)
    email = models.EmailField()

    def __str__(self):
        return self.email
