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

from login.models import User
from .models import CommercialUser
from premium_user.models import AddGroup

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

class EditProfileForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    date_of_birth = forms.DateTimeField(widget=forms.TextInput(attrs={'class':'datetime-input'}))
    gender = forms.ChoiceField(choices=[(1, 'Male'), (2, 'Female'), (3, 'Transgender')],
    widget = forms.RadioSelect)
    phone = PhoneNumberField(widget=forms.TextInput(), required=False)
    
    class Meta:
        # model = User
        fields = [ 'first_name', 'last_name', 'date_of_birth', 'gender', 'phone' ]

class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    class Meta:
        # model
        fields = ['amount']

class SendMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    def __init__(self, user, *args, **kwargs):
        super(SendMoneyForm, self).__init__(*args, **kwargs)
        self.fields['send_to'] = forms.ChoiceField(
            choices=[(friend, User.objects.get(username=friend).first_name + " " + User.objects.get(username=friend).last_name) for friend in Friend.objects.get(username=user).friend_list]
        )

    class Meta:
        # model
        fields = ['send_to', 'amount']

class RequestMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    def __init__(self, user, *args, **kwargs):
        super(RequestMoneyForm, self).__init__(*args, **kwargs)
        self.fields['request_from'] = forms.ChoiceField(
            choices=[(friend, User.objects.get(username=friend).first_name + " " + User.objects.get(username=friend).last_name) for friend in Friend.objects.get(username=user).friend_list]
        )

    class Meta:
        # model
        fields = ['request_from', 'amount']

class CreatePagesForm(forms.Form):
    page_title = forms.CharField(max_length=50, required=True, widget=forms.Textarea(attrs={'cols':50,'rows':1}))
    page_description = forms.CharField(max_length=250, required=True, widget=forms.Textarea(attrs={'cols':50,'rows':15}))
    
    class Meta:
        #model = Pages
        fields = [ 'page_title', 'page_description' ]

#class CreatePagesDetailForm(forms.Form):
 #   author = forms.CharField(max_length=30)
  #  page_title = forms.CharField(max_length=50, required=True, widget=forms.Textarea(attrs={'cols':50,'rows':1}))
   # page_description = forms.CharField(max_length=250, required=True, widget=forms.Textarea(attrs={'cols':50,'rows':15}))
    #page_link = forms.CharField(max_length=100)
    
    #class Meta:
        #model = Pages
     #   fields = [ 'author', 'page_title', 'page_description', 'page_link' ]
class AddMoneyNewForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=5000, required=False)

    class Meta:
        # model
        fields = ['amount']

class VerifyPanForm(forms.Form):
    pan_Card_Number = forms.IntegerField(min_value=10000000, max_value=99999999, required=False)
    
    class Meta:
        # model
        fields = ['pan_Card_Number']
