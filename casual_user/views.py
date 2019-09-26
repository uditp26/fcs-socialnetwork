from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from .models import CasualUser, Post, Friend
from login.models import User

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms


from datetime import datetime

def savePost(self, request, current_user):

    post = request.POST.dict()['postarea']
    scope = request.POST.dict()['level']

    timestamp = datetime.now(tz=None)
    user_posts = Post.objects.filter(username = str(current_user))

    if len(user_posts) > 0:

        if scope == "0":
            user_posts[0].private_posts.append(post)
            user_posts[0].prv_timestamp.append(timestamp)
        elif scope == "1":
            user_posts[0].friends_posts.append(post)
            user_posts[0].frnd_timestamp.append(timestamp)

        user_posts[0].save()
    else:
        if scope == "0":
            new_post = Post(username=str(current_user), private_posts = [post], friends_posts = [], prv_timestamp = [timestamp], frnd_timestamp = [])
        elif scope == "1":
            new_post = Post(username=str(current_user), private_posts = [], friends_posts = [post], prv_timestamp = [], frnd_timestamp = [timestamp])
        new_post.save()


def genBundle(current_user):
    casual_user = CasualUser.objects.get(user=current_user)
    bundle = dict()
    name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
    user_posts = Post.objects.filter(username=str(current_user))
    # use post 'level' information
    all_posts = None

    pposts = []

    if len(user_posts) > 0:
        pposts = list(reversed(user_posts[0].private_posts))   # reverses the list

    # fetch friends' posts

    friends = Friend.objects.filter(username = str(current_user))

    f_posts = []

    if len(friends) > 0:

        for frnd in friends:
            fp = Post.objects.filter(username=frnd)

            if len(fp) > 0:
                f_posts += list(reversed(fp[0].friends_posts))

    all_posts = pposts + f_posts

    bundle = {'name': name, 'posts':all_posts}
    return bundle

class HomepageView(View):
    template_name = 'casual_user/homepage.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            bundle = genBundle(current_user)
            return render(request, self.template_name, {'bundle':bundle})

    def post(self, request):
        current_user = request.user
        savePost(self, request, current_user)
        bundle = genBundle(current_user)
        return render(request, self.template_name, {'bundle':bundle})

class ProfileView(View):
    template_name = 'casual_user/myprofile.html'

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


class ListUserView(View):
    template_name = 'casual_user/list_user.html'
    
    def get(self, request):
        current_user = request.user
        username1 = current_user.username
        
        try:
            have_friend = Friend.objects.get(username = username1)
            current_user_friendlist  = list(have_friend.friend_list)

        except:
            current_user_friendlist = []

        search_name = findfriend(request).lower()
        print("search name : ", search_name)

        user_name_list = User.objects.filter(first_name = search_name)
        user_name_list = user_name_list.exclude(username = current_user.username)

        bundle = dict()
        for user in user_name_list:
            if user.username in current_user_friendlist:
                bundle[user] = 0
            else:
                bundle[user] = 1

        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):

        current_user = request.user

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
        user_name_list = User.objects.filter(first_name = search_name)
        user_name_list = user_name_list.exclude(username = current_user.username)

        print("Old_friend_list = ", current_user_friendlist)

        for i in user_name_list:
            print(request.POST.dict())
            try:
                if request.POST.dict()[i.username] == "Add Friend":
                    print("selected_button", i.username)
                    
                    have_friend.friend_list.append(i.username)
                    have_friend.save()

                    break
                elif request.POST.dict()[i.username] == "Unfriend":
                    print("selected_button", i.username)

                    have_friend.friend_list.remove(i.username)
                    have_friend.save()

                    break
            except:
                pass
            
        try:
            have_friend = Friend.objects.get(username = username1)
            current_user_friendlist  = list(have_friend.friend_list)

        except:
            have_friend = Friend()
            have_friend.username = username1
            current_user_friendlist = []
            have_friend.friend_list = current_user_friendlist
        
        search_name = findfriend(request).lower()
        user_name_list = User.objects.filter(first_name = search_name)
        user_name_list = user_name_list.exclude(username = current_user.username)

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
