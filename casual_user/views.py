from django.shortcuts import render, reverse
from django.views.generic import View
from django.http import Http404

from .models import CasualUser, Post, Friend
from login.models import User

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect

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