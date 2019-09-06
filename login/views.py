from django.shortcuts import render
from .forms import LoginForm, RegistrationForm
from django.views.generic import View

# Create your views here.


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

        if form.is_valid():
            pass

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
        form = self.form_class(request.POST)
        
        if form.is_valid():
            pass

        return render(request, self.template_name, {'form': form})