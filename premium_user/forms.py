from django.contrib.auth.forms import UserCreationForm
from django import forms

import unicodedata

from django import forms
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.contrib.auth.hashers import (
    UNUSABLE_PASSWORD_PREFIX, identify_hasher,
)

from django.conf import settings

from .models import User, AddGroup

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

class AddGroupForm(forms.Form):
    name = forms.CharField(max_length=50)
    gtype = forms.ChoiceField(choices=[(1, 'Free'), (2, 'Premium')],widget = forms.RadioSelect)
    price = forms.FloatField()

    class Meta:
        model = AddGroup
        fields = [ 'name', 'gtype', 'price']

