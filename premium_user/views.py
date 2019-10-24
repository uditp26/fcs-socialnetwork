from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from login.models import User
from .models import PremiumUser, AddGroup, Group, GroupRequest

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from datetime import datetime
from .forms import AddGroupForm

class ProfileView(View):
    template_name = 'premium_user/myprofile.html'

    def get(self, request):
        current_user = request.user

        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = PremiumUser.objects.get(user=current_user)
            
            bundle = dict()
            name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            bundle = {'name': name, 'date_of_birth': casual_user.date_of_birth, 'gender': casual_user.gender,'phone': casual_user.phone}
            return render(request, self.template_name, {'current_user':bundle})

class AddGroupFormView(View):
    form_class = AddGroupForm
    template_name = 'premium_user/addgroup_form.html'
    
    #display blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    #put data inside blank text fields 
    def post(self, request):
        current_user = request.user
        form = self.form_class(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            gtype = form.cleaned_data['gtype']
            price = form.cleaned_data['price']

            addgroup = AddGroup(admin=current_user.username, name=name, gtype=gtype, price=price)
            addgroup.members = []
            addgroup.members.append(current_user.username)
            addgroup.save()

            try:
                group = Group.objects.get(admin = current_user.username)
                group.group_list.append(addgroup.name)
                group.save()

            except:
                group = Group()
                group.admin = current_user.username
                group.group_list = []
                group.group_list.append(addgroup.name)
                group.save()

        return render(request, self.template_name, {'form': form})

def return_bundle_for_request(current_user):
    current_request = GroupRequest.objects.filter(admin = current_user.username)
    key = 1
    bundle = {}
    group_request = []
    for i in current_request:
        name = i.name
        for member in i.members:
            temp={}
            temp[name] = member
            bundle[key] = temp
            group_request.append([key, name, member])
            key = key + 1
            
    return bundle, group_request

class ListRequestView(View):
    template_name = 'premium_user/listrequest.html'
    
    def get(self, request):
        current_user = request.user
        bundle, group_request = return_bundle_for_request(current_user)

        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        bundle, group_request = return_bundle_for_request(current_user)

        for value in group_request:
            try:
                if request.POST.dict()[str(value[0])] == "accept":
                    name = value[1]; member = value[2]
                    admin = current_user.username

                    #remove entry from grouprequest
                    group = GroupRequest.objects.get(admin = admin, name = name)
                    group.members.remove(member)
                    group.save()
                    
                    #add member in add_group model
                    add_group = AddGroup.objects.get(admin = admin, name = name)
                    add_group.members.append(member)
                    add_group.save()
                    break
                       
                elif request.POST.dict()[str(value[0])] == "reject":
                    name = value[1]; member = value[2]
                    admin = current_user.username
                    group = GroupRequest.objects.get(admin = admin, name = name)
                    group.members.remove(member)
                    group.save()
                    break

            except:
                pass

        bundle, group_request = return_bundle_for_request(current_user)
        return render(request, self.template_name, {'bundle': bundle})

class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))