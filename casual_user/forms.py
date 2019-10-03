from django import forms
from .models import Friend
from login.models import User


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