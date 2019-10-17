from django import forms
from .models import Friend
from login.models import User
from phonenumber_field.formfields import PhoneNumberField


class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    class Meta:
        # model
        fields = ['amount']

class SendMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    def __init__(self, user, *args, **kwargs):
        super(SendMoneyForm, self).__init__(*args, **kwargs)
        try:
            self.fields['send_to'] = forms.ChoiceField(
                choices=[(friend, User.objects.get(username=friend).first_name + " " + User.objects.get(username=friend).last_name) for friend in Friend.objects.get(username=user).friend_list]
            )
        except:
            self.fields['send_to'] = forms.ChoiceField(choices=[])

    class Meta:
        # model
        fields = ['send_to', 'amount']

class RequestMoneyForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, min_value=0)

    def __init__(self, user, *args, **kwargs):
        super(RequestMoneyForm, self).__init__(*args, **kwargs)
        try:
            self.fields['request_from'] = forms.ChoiceField(
                choices=[(friend, User.objects.get(username=friend).first_name + " " + User.objects.get(username=friend).last_name) for friend in Friend.objects.get(username=user).friend_list]
            )
        except:
            self.fields['request_from'] = forms.ChoiceField(choices=[])

    class Meta:
        # model
        fields = ['request_from', 'amount']

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

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=4, widget=forms.NumberInput())

    class Meta:
        fields = ['otp']