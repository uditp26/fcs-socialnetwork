from django.views import View
from django.shortcuts import render, redirect, HttpResponseRedirect, reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.views import generic
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django import forms

from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import resolve_url
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from urllib.parse import urlparse, urlunparse

from .forms import LoginForm, RequestpwdForm, ResetpwdForm, RegistrationForm, PasswordResetForm, SetPasswordForm

from .models import User, FailedLogin

from casual_user.models import CasualUser, Wallet
from premium_user.models import PremiumUser, GroupPlan

import time

UserModel = get_user_model()

def createNewUser(email, password, first_name, last_name, u_type):
    username = email.split('@')[0]

    # check for unique username
    similar_users = len(User.objects.filter(username=username))

    if similar_users != 0:
        new_username = username + '_' + str(similar_users)
        i = 0
        while len(User.objects.filter(username=new_username)) != 0:
            i += 1
            new_username = username + '_' + str(similar_users + i)
        username = new_username

    new_user = User(username=username, email=email, first_name=first_name, last_name=last_name, user_type = u_type)
    new_user.set_password(password)
    new_user.save()

    return new_user, username
class LoginFormView(View):
    form_class = LoginForm
    template_name = 'login/login_form.html'

    # displays a blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})
                                   
    # process form data
    def post(self, request):
        form = self.form_class(request.POST)

        radio_btn = request.POST.get('radio_btn')

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # returns user objects if credentials are correct

            user = authenticate(username=username, password=password)

            if user is not None:

                if user.is_active and int(radio_btn) == user.user_type:
                    login(request, user)
                    # redirect to respective page
                    
                    # if radio_btn == '1':
                    #     return redirect('casual_user:homepage')
                    # elif radio_btn == '2':
                    #     return redirect('premium_user:myprofile')

                    f_list = FailedLogin.objects.filter(username=username)

                    if len(f_list) > 0:
                        curr_time = time.time()

                        if f_list[0].next_login > curr_time:
                            form.add_error('username', "Access Denied. Backoff.")
                        else:
                            FailedLogin.objects.filter(username=username).delete()
                            login(request, user)

                            # redirect to respective page
                            if radio_btn == '1':
                                return redirect('casual_user:homepage')
                            elif radio_btn == '2':
                                return redirect('premium_user:homepage')
                            else:
                                return redirect('')
                    else:
                        login(request, user)

                        # redirect to respective page
                        if radio_btn == '1':
                            return redirect('casual_user:homepage')
                        # elif radio_btn == '2':
                        #     return redirect('premium_user:homepage')
                        
                        elif radio_btn == '2':
                            try:
                                GroupPlan.objects.get(customer = username)
                                wallet = Wallet.objects.get(username = username)
                                wallet.transactions_left = 30
                                wallet.save()
                                
                                return redirect('premium_user:homepage')
                            except:
                                return redirect('premium_user:groupplanforreg')

                        else:
                            return redirect('')
                else:
                    form.add_error('username', "User does not exist.")
            else:
                timestamp = time.time()
                f_list = FailedLogin.objects.filter(username=username)
                if len(f_list) == 0:
                    FailedLogin(username=username, count=1, last_login=timestamp, next_login=timestamp).save()
                    form.add_error('username', "User credentials did not match existing records.")
                else:
                    if f_list[0].last_login < f_list[0].next_login:
                        form.add_error('username', "Access Denied. Backoff for 3 mins.")
                    else:
                        if f_list[0].count == 3:
                            f_list[0].count = 0 
                            f_list[0].last_login = timestamp
                            new_timestamp = timestamp + 180
                            f_list[0].next_login = new_timestamp
                        else:
                            f_list[0].count += 1
                            f_list[0].last_login = timestamp
                            f_list[0].next_login = timestamp
                        f_list[0].save()
                        form.add_error('username', "User credentials did not match existing records.")
        return render(request, self.template_name, {'form': form})

class RegistrationFormView(View):
    form_class = RegistrationForm
    template_name = 'login/registration_form.html'
    
    #display blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    #put data inside blank text fields 
    def post(self, request):
        # current_user = request.user
        form = self.form_class(request.POST)
        
        if form.is_valid():
            account_type = form.cleaned_data['account_type']

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            date_of_birth = form.cleaned_data['date_of_birth']
            gender = form.cleaned_data['gender']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            new_user, username = createNewUser(email, password, first_name, last_name, int(account_type))

            if account_type == '1':
                c_user = CasualUser(user=new_user, date_of_birth=date_of_birth, gender=gender, phone=phone, email=email)
                c_user.save()
                Wallet(username=username, user_type=int(account_type), amount=0.0, transactions_left=15).save()
                return render(request, 'login/registrationsuccess.html', {'username': username})
            elif account_type == '2':
                p_user = PremiumUser(user=new_user, date_of_birth=date_of_birth, gender=gender, phone=phone, email=email)
                p_user.save()
                # add entry to premium user table
                wallet = Wallet(username=username, user_type=int(account_type), amount=0.0, transactions_left=30)
                wallet.save()
                return HttpResponseRedirect(reverse('login:login'))    
                
            else:
                # add entry to commercial user table
                Wallet(username=username, user_type=int(account_type), amount=0.0, transactions_left=10000).save()
                return render(request, 'login/registrationsuccess.html', {'username': username})

        return render(request, self.template_name, {'form': form})

class RegistrationSuccessView(View):
    template_name = 'login/registrationsuccess.html'

    def get(self, request):
        return render(request, self.template_name)

# Class-based password reset views
# - PasswordResetView sends the mail
# - PasswordResetDoneView shows a success message for the above
# - PasswordResetConfirmView checks the link the user clicked and
#   prompts for a new password
# - PasswordResetCompleteView shows a success message for the above

class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context

class PasswordResetView(PasswordContextMixin, FormView):
    template_name = 'login/password_reset_form.html'
    email_template_name = 'login/password_reset_email.html'
    extra_email_context = None
    form_class = PasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'login/password_reset_subject.txt'
    success_url = reverse_lazy('login:password_reset_done')
    title = _('Password reset')
    token_generator = default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super().form_valid(form)


INTERNAL_RESET_URL_TOKEN = 'set-password'
INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class PasswordResetDoneView(PasswordContextMixin, TemplateView):
    template_name = 'login/password_reset_done.html'
    title = _('Password reset sent')


class PasswordResetConfirmView(PasswordContextMixin, FormView):
    template_name = 'login/password_reset_confirm.html'
    form_class = SetPasswordForm
    post_reset_login = False
    post_reset_login_backend = None
    success_url = reverse_lazy('login:password_reset_complete')
    title = _('Enter new password')
    token_generator = default_token_generator

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs['uidb64'])

        if self.user is not None:
            token = kwargs['token']
            if token == INTERNAL_RESET_URL_TOKEN:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, INTERNAL_RESET_URL_TOKEN)
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        if self.post_reset_login:
            auth_login(self.request, user, self.post_reset_login_backend)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        else:
            context.update({
                'form': None,
                'title': _('Password reset unsuccessful'),
                'validlink': False,
            })
        return context


class PasswordResetCompleteView(PasswordContextMixin, TemplateView):
    template_name = 'login/password_reset_complete.html'
    title = _('Password reset complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_url'] = resolve_url(settings.LOGIN_URL)
        return context

class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect('login:login')
