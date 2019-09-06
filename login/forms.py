from django import forms
from django.contrib.auth.models import User

class LoginForm(forms.Form):
	username = forms.CharField(max_length=50)
	password = forms.CharField(widget=forms.PasswordInput)

	class Meta:
		model = User
		fields = ['username', 'password']

class RegistrationForm(forms.Form):
	first_name = forms.CharField(max_length=50)
	last_name = forms.CharField(max_length=50)
	date_of_birth = forms.DateTimeField(widget=forms.TextInput(attrs={'class':'datetime-input'}))
	gender = forms.ChoiceField(choices=[(1, 'Male'), (2, 'Female'), (3, 'Transgender')],
	widget = forms.RadioSelect)
	email = forms.CharField(widget=forms.EmailInput)
	password = forms.CharField(widget=forms.PasswordInput)
	account_type = forms.ChoiceField(choices=[(1, 'Casual'), (2, 'Premium'), (3, 'Commercial')],
	widget = forms.RadioSelect)

	class Meta:
		model = User
		fields = [ 'first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'password', 'account_type']