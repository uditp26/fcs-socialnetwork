from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from .models import CasualUser, Friend
from login.models import User

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms


class HomepageView(View):
    template_name = 'casual_user/homepage.html'

    def get(self, request):
        current_user = request.user
       
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CasualUser.objects.get(user=current_user)
            bundle = dict()
            name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            bundle = {'name': name, 'date_of_birth': casual_user.date_of_birth, 'gender': casual_user.gender,'phone': casual_user.phone}
            return render(request, self.template_name, {'current_user':bundle})

class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))


def findfriend(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
    return q

#function that return search user/users list, friend_list and current user friend object
def user_friendlist(current_user, request):
    username1 = current_user.username
    try:
        have_friend = Friend.objects.get(username = username1)
        current_user_friendlist  = list(have_friend.friend_list)

    except:
        have_friend = Friend()
        have_friend.username = username1
        current_user_friendlist = []
        have_friend.friend_list = current_user_friendlist

    search_name = findfriend(request).lower()
    print("search name : ", search_name)

    user_name_list = User.objects.filter(first_name = search_name)
    user_name_list = user_name_list.exclude(username = current_user.username)

    return user_name_list, current_user_friendlist, have_friend


class ListUserView(View):
    template_name = 'casual_user/list_user.html'
    
    def get(self, request):
        current_user = request.user
        user_name_list, current_user_friendlist, have_friend = user_friendlist(current_user, request)
        
        bundle = dict()
        for user in user_name_list:
            if user.username in current_user_friendlist:
                bundle[user] = 0
            else:
                bundle[user] = 1

        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
    
        user_name_list, current_user_friendlist, have_friend = user_friendlist(current_user, request)

        print("Old_friend_list = ", current_user_friendlist)

        for i in user_name_list:
            print(request.POST.dict())
            try:
                selected_user = i.username
                if request.POST.dict()[selected_user] == "Add Friend":
                    print("selected_button", selected_user)
                    
                    have_friend.friend_list.append(selected_user)
                    have_friend.save()

                    #for implementation of bi-direction add_friend
                    try:
                        b_user_friendlist = Friend.objects.get(username = selected_user)
                        b_user_friendlist.friend_list.append(current_user.username)
                        b_user_friendlist.save()
                        print("b_user_friendlist = ", b_user_friendlist.friend_list)
                    except:
                        b_user_friendlist = Friend()
                        b_user_friendlist.username = selected_user
                        current_user_friendlist = []
                        b_user_friendlist.friend_list = current_user_friendlist
                        b_user_friendlist.friend_list.append(current_user.username)
                        b_user_friendlist.save()
                        print("b_user_friendlist = ", b_user_friendlist.friend_list)
                    break

                elif request.POST.dict()[selected_user] == "Unfriend":
                    print("selected_button", selected_user)

                    have_friend.friend_list.remove(selected_user)
                    have_friend.save()

                    #for implementation of bi-direction remove_friend
                    b_user_friendlist = Friend.objects.get(username = selected_user)
                    b_user_friendlist.friend_list.remove(current_user.username)
                    b_user_friendlist.save()

                    break
            except:
                pass
            
        user_name_list, current_user_friendlist, have_friend = user_friendlist(current_user, request)

        print("updated_friend_list = ", current_user_friendlist)
        bundle = dict()
        for user in user_name_list:
            if user.username in current_user_friendlist:
                bundle[user] = 0
            else:
                bundle[user] = 1

        return render(request, self.template_name, {'bundle': bundle})


#for display friendlist
class FriendView(View):
    template_name = 'casual_user/friend.html'

    def get(self, request):
        current_user = request.user
        username1 = current_user.username

        try:
            have_friend = Friend.objects.get(username = username1)
            current_user_friendlist  = list(have_friend.friend_list)

        except:
            current_user_friendlist = []

        current_user = dict()
        current_user[username1] = current_user_friendlist
        return render(request, self.template_name, {'current_user': current_user})

    def post(self, request):
        current_user = request.user
        username1 = current_user.username

        try:
            have_friend = Friend.objects.get(username = username1)
            current_user_friendlist  = list(have_friend.friend_list)

        except:
            current_user_friendlist = []
            
        for i in current_user_friendlist:
            print(request.POST.dict())
            try:
                selected_user = i
                
                if request.POST.dict()[selected_user] == "Unfriend":
                    have_friend.friend_list.remove(selected_user)
                    have_friend.save()

                    #for implementation of bi-direction remove_friend
                    b_user_friendlist = Friend.objects.get(username = selected_user)
                    b_user_friendlist.friend_list.remove(current_user.username)
                    b_user_friendlist.save()

                    break
            except:
                pass

        try:
            have_friend = Friend.objects.get(username = username1)
            current_user_friendlist  = list(have_friend.friend_list)

        except:
            current_user_friendlist = []
            
        current_user = dict()
        current_user[username1] = current_user_friendlist

        return render(request, self.template_name, {'current_user': current_user})

