from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from login.models import User
from .models import PremiumUser, AddGroup, Group, GroupRequest, GroupPlan, Message
from casual_user.models import Wallet, Transaction, Request, Post, Friend, FriendRequest, CasualUser, Timeline
from .forms import AddGroupForm, GroupPlanForm, AddMoneyForm, SendMoneyForm, RequestMoneyForm, EditProfileForm, OTPVerificationForm, SubscriptionForm

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from datetime import datetime
from datetime import date

from django.utils import timezone
import pytz

import sys

import time
from django.core.mail import send_mail
import hashlib

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

#! pip install cryptograhy
#! pip install pycrypto
#! pip install pycryptodome
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5

decorators = [cache_control(no_cache=True, must_revalidate=True, no_store=True), login_required(login_url='http://127.0.0.1:8000/login/')]

def decryptcipher(cipher, username):
    encObj = Encryption.objects.get(user= username)
    prvkey = encObj.privatekey
    prvkey = prvkey.replace("\\\\n","\n")

    ciphertext_new = cipher.encode('utf-8')
    ciphertext_new = ciphertext_new.decode('unicode-escape').encode('ISO-8859-1')

    keyPriv = RSA.importKey(prvkey)
    cipher = Cipher_PKCS1_v1_5.new(keyPriv)

    decrypt_text = cipher.decrypt(ciphertext_new, None).decode()
    print("decrypted msg->", decrypt_text)
    return decrypt_text

def priceofplan(plantype):
    if plantype == 1:
        price = 50
        noofgroup = 2
    elif plantype == 2:
        price = 100
        noofgroup = 4
    else:
        price = 150
        noofgroup = sys.float_info.max      # stored as 10,000 in form/model field
    return price, noofgroup

def get_user_info(current_user):
    if current_user.user_type == 1:
        login_user = CasualUser.objects.get(user=current_user)
    elif current_user.user_type == 2:
        login_user = PremiumUser.objects.get(user=current_user)
    else:
        login_user = CommercialUser.objects.get(user=current_user)
    return login_user

def savePost(request, current_user, visitor=""):

    post = request.POST.dict()['postarea']
    # call below function to decrypt(after package install)
    try:
        post =  decryptcipher(current_user, post) 
    except:
        print("ERROR IN PKI")
        pass
    scope = request.POST.dict()['level']

    if visitor != "":
        visitor = User.objects.get(username=visitor).first_name + " " + User.objects.get(username=visitor).last_name
        post += " \t\t\t Posted By: " + str(visitor)

    timestamp = timezone.now()
    user_posts = Post.objects.filter(username = str(current_user))

    if len(user_posts) > 0:
        if scope == "0":
            user_posts[0].friends_posts.append(post)
            user_posts[0].frnd_timestamp.append(timestamp)
        elif scope == "1":
            user_posts[0].public_posts.append(post)
            user_posts[0].pblc_timestamp.append(timestamp)

        user_posts[0].save()
    else:
        if scope == "0":
            new_post = Post(username=str(current_user), friends_posts = [post], public_posts = [], frnd_timestamp = [timestamp], pblc_timestamp = [])
        elif scope == "1":
            new_post = Post(username=str(current_user), friends_posts = [], public_posts = [post], frnd_timestamp = [], pblc_timestamp = [timestamp])
        new_post.save()


def genBundle(current_user):
    login_user = get_user_info(current_user)
    bundle = dict()
    name = login_user.user.first_name + ' ' +  login_user.user.last_name
    user_posts = Post.objects.filter(username=str(current_user))
    # use post 'level' information
    all_posts = None

    pposts = []

    if len(user_posts) > 0:
        pposts = list(reversed(user_posts[0].friends_posts))
        pposts += list(reversed(user_posts[0].public_posts))   # reverses the list

    # fetch friends' posts

    f_user = Friend.objects.filter(username = str(current_user))

    f_posts = []

    if len(f_user) > 0:

        friends = f_user[0].friend_list

        for frnd in friends:
            fp = Post.objects.filter(username=frnd)

            if len(fp) > 0:
                f_posts += list(reversed(fp[0].friends_posts))

    p_posts = []

    all_user_posts = Post.objects.exclude(username=str(current_user))

    for post in all_user_posts:

        if len(post.public_posts) > 0:
            p_posts.append(post.public_posts[-1])

    all_posts = pposts + f_posts + p_posts

    bundle = {'name': name, 'posts':all_posts}
    return bundle

def updateExistingUser(curr_user, first_name, last_name, dob, phone):
    curr_user.first_name = first_name
    curr_user.last_name = last_name
    curr_user.save()
    
    if curr_user.user_type == 1:
        curr_user = CasualUser.objects.get(user=curr_user)
    elif curr_user.user_type == 2:
        curr_user = PremiumUser.objects.get(user=curr_user)
    else:
        curr_user = CommercialUser.objects.get(user=curr_user)
    curr_user.date_of_birth = dob
    curr_user.phone = phone
    curr_user.save()

@method_decorator(decorators, name='dispatch')
class HomepageView(View):
    template_name = 'premium_user/homepage.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        elif PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        else:
            bundle = genBundle(current_user)
            return render(request, self.template_name, {'bundle':bundle})

    def post(self, request):
        current_user = request.user
        savePost(request, current_user)
        bundle = genBundle(current_user)
        return HttpResponseRedirect(reverse('premium_user:homepage'))

#___________________________________________________group_________________________________________
#pass to groupdetails.html
def getgroupdetails(current_user):
    bundle = {}
    try:
        groups = AddGroup.objects.filter(admin = current_user.username)
        groupplan = GroupPlan.objects.get(customer = current_user.username)

        groupinfo = {}
        key = 1; anotherkey  = 11
        for group in groups:
            m = ""; members = group.members
            for i in members:
                user = User.objects.get(username = i )
                name = str(user.first_name)+' '+str(user.last_name)
                m = m + " " + "'"+name+"'"
            temp1 = {}; temp1[group.price] = m
            temp2 = {}; temp2[group.name] = temp1
            groupinfo[key] = temp2
            key+=1
        groupplaninfo = {}
        current_date = datetime.now().date()
        rechargedate = groupplan.recharge_on.date()
        days = 30 - int((current_date - rechargedate).days)
        noofgroups = int(groupplan.noofgroup)
        groupplaninfo[days] = noofgroups
        bundle[anotherkey] = groupinfo; anotherkey += 1
        bundle[anotherkey] = groupplaninfo
    except:
        bundle = {}
        pass
    return bundle

@method_decorator(decorators, name='dispatch')       
class GroupDetailsView(View):
    template_name = 'premium_user/groupdetails.html'

    def get(self, request):
        current_user = request.user

        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))

        bundle = getgroupdetails(current_user)
        return render(request, self.template_name, {'bundle':bundle})

@method_decorator(decorators, name='dispatch')
class ProfileView(View):
    template_name = 'premium_user/myprofile.html'

    def get(self, request):
        current_user = request.user

        if str(current_user) is 'AnonymousUser':
            raise Http404
        elif PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        else:
            login_user = get_user_info(current_user)
            bundle = dict()
            #name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            fname = login_user.user.first_name
            lname = login_user.user.last_name
            gender = login_user.gender
            if gender==1:
                gender = str("Male")
            elif gender==2:
                gender = str("Female")
            elif gender==3:
                gender = str("Transgender")
            bundle = {'First Name': fname, 'Last Name': lname,'Date of Birth': login_user.date_of_birth, 'Gender': gender, 'Email':login_user.email, 'Phone': login_user.phone}
            return render(request, self.template_name, {'current_user':bundle})

@method_decorator(decorators, name='dispatch')
class EditProfileFormView(View):
    form_class = EditProfileForm
    template_name = 'premium_user/editprofile.html'
    
    def get(self, request):
        current_user = request.user
        form = self.form_class(None)

        if str(current_user) is 'AnonymousUser':
            raise Http404
        elif PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        else:
            login_user = get_user_info(current_user)
            fname = login_user.user.first_name
            lname = login_user.user.last_name
            dob = login_user.date_of_birth
            phoneno = login_user.phone
            form.fields['first_name'].initial = fname
            form.fields['last_name'].initial = lname
            form.fields['date_of_birth'].initial = dob
            form.fields['phone'].initial = phoneno
            return render(request, self.template_name, {'form':form})

    def post(self, request):
        current_user = request.user
        form = self.form_class(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            dob = form.cleaned_data['date_of_birth']
            phone = form.cleaned_data['phone']
            updateExistingUser(current_user, first_name, last_name, dob, phone)
            return HttpResponseRedirect('')
        return render(request, self.template_name, {'form':form})


#___________________________________________________show userdetails(By dynamic url)___________________________
@method_decorator(decorators, name='dispatch')
class UserProfileView(View):
    template_name = 'premium_user/userprofile.html'

    def get(self, request, username):
        user = User.objects.get(username=username)
        fname = user.first_name
        lname = user.last_name
        
        if user.user_type == 1:         # casual-user
            casual_user = CasualUser.objects.get(user=user)
            dob = casual_user.date_of_birth
            gender = casual_user.gender
            email = casual_user.email
        elif user.user_type == 2:       #premium-user
            premium_user = PremiumUser.objects.get(user=user)
            dob = premium_user.date_of_birth
            gender = premium_user.gender
            email = premium_user.email
        else:                           #commercial-user
            commercial_user = CommercialUser.objects.get(user=user)
            dob = commercial_user.date_of_birth
            gender = commerical_user.gender
            email = commercial_user.email
        
        bundle = {'First Name': fname, 'Last Name':lname, 'Date of Birth': dob, 'Gender':gender,'Email':email}
        return render(request, self.template_name, {'bundle': bundle})

#__________________________________________Make Friend and Find Friend & Group_______________________________________________
def findfriend(request):
    q=""
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
    return q

def findGroup(request):
    q=""
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
        current_user_friendlist = []

    search_name = findfriend(request).lower()

    user_name_list = User.objects.filter(first_name__icontains = search_name)
    user_name_list = user_name_list.exclude(username = current_user.username)

    bundle = dict()
    if user_name_list:
        for user in user_name_list:
            try:
                requestto = FriendRequest.objects.get(requestto = user.username)
                requestlist = requestto.requestfrom
            except:
                requestlist = []

            if user.username in current_user_friendlist:
                name = str(user.first_name) + ' ' + str(user.last_name)
                status = 0; temp = {}; temp[name] = status
                bundle[user] = temp
                
            elif current_user.username in requestlist:
                name = str(user.first_name) + ' ' + str(user.last_name)
                status = 1; temp = {}; temp[name] = status
                bundle[user] = temp
            else:
                name = str(user.first_name) + ' ' + str(user.last_name)
                status = 2; temp = {}; temp[name] = status
                bundle[user] = temp
    else:
        bundle = dict()

    return bundle, user_name_list

@method_decorator(decorators, name='dispatch')
class ListUserView(View):
    template_name = 'premium_user/list_user.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        bundle, user_name_list = user_friendlist(current_user, request)
        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        bundle, user_name_list = user_friendlist(current_user, request)

        for i in user_name_list:
            try:
                selected_user = i.username
                if request.POST.dict()[selected_user] == "Add Friend":
                    try:
                        try:
                            requestto1 = FriendRequest.objects.get(requestto = current_user.username)
                            if selected_user in requestto1.requestfrom:
                                return redirect('premium_user:friendrequest')
                        except:
                            pass
                        requestto = FriendRequest.objects.get(requestto = selected_user)
                        requestto.requestfrom.append(current_user.username)
                        requestto.save()
                        break
                    except:
                        FriendRequest(requestto = selected_user, requestfrom = [current_user.username]).save()
                        break

                elif request.POST.dict()[selected_user] == "Unfriend":
                    have_friend = Friend.objects.get(username = current_user.username)
                    have_friend.friend_list.remove(selected_user)
                    have_friend.save()

                    #for implementation of bi-direction remove_friend
                    b_user_friendlist = Friend.objects.get(username = selected_user)
                    b_user_friendlist.friend_list.remove(current_user.username)
                    b_user_friendlist.save()
                    break
            except:
                pass
        bundle, user_name_list = user_friendlist(current_user, request)
        return HttpResponseRedirect(reverse('premium_user:listuser'))

@method_decorator(decorators, name='dispatch')
class FriendRequestView(View):
    template_name = 'premium_user/listfriendrequest.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        try:
            friendrequestObj = FriendRequest.objects.get(requestto = current_user.username)
            friendlist = friendrequestObj.requestfrom
            friendBundle = {}
            for username in friendlist:
                userObj = User.objects.get(username = username)
                name = str(userObj.first_name) + ' ' +  str(userObj.last_name)
                friendBundle[username] = name
        except:
            friendBundle = {}
        return render(request, self.template_name, {'friendBundle': friendBundle})

    def post(self, request):
        current_user = request.user
        friendrequestObj = FriendRequest.objects.get(requestto = current_user.username)
        friendlist = friendrequestObj.requestfrom
        for i in friendlist:
            try:
                selected_user = i
                if request.POST.dict()[str(i)] == "accept":
                    friendrequestObj = FriendRequest.objects.get(requestto = current_user.username)
                    friendrequestObj.requestfrom.remove(selected_user)
                    friendrequestObj.save()
                    try:
                        friendObj = Friend.objects.get(username = current_user.username)
                        friendObj.friend_list.append(selected_user)
                        friendObj.save()
                    except:
                        Friend(username = current_user.username, friend_list = [selected_user]).save()
                    # for implementation of bi-direction add_friend
                    try:
                        b_user_friendlist = Friend.objects.get(username = selected_user)
                        b_user_friendlist.friend_list.append(current_user.username)
                        b_user_friendlist.save()
                    except:
                        b_user_friendlist = Friend()
                        b_user_friendlist.username = selected_user
                        current_user_friendlist = []
                        b_user_friendlist.friend_list = current_user_friendlist
                        b_user_friendlist.friend_list.append(current_user.username)
                        b_user_friendlist.save()
                    break
                elif request.POST.dict()[str(i)] == "reject":
                    friendrequestObj = FriendRequest.objects.get(requestto = current_user.username)
                    friendrequestObj.requestfrom.remove(selected_user)
                    friendrequestObj.save()
                    break
            except:
                pass
        return HttpResponseRedirect(reverse('premium_user:friendrequest'))

def showfrndlist(username1):
    try:
        have_friend = Friend.objects.get(username = username1)
        current_user_friendlist  = list(have_friend.friend_list)
        
        name_of_friendlist = []
        for i in current_user_friendlist:
            user = User.objects.get(username = i)
            name = str(user.first_name) + ' ' + str(user.last_name)
            name_of_friendlist.append(name)

    except:
        have_friend = Friend() 
        current_user_friendlist = []

    current_user = []
    if current_user_friendlist:
        current_user = zip(current_user_friendlist, name_of_friendlist)
    else:
        current_user = []

    return current_user, have_friend

def checkPrivacySettings(friends_zip):
    level_list = []
    uname_list = []
    name_list = []
    for username, name in friends_zip:
        uname_list.append(username)
        name_list.append(name)
        level_list.append(str(Timeline.objects.get(username=username).level))

    return zip(uname_list, name_list, level_list)

#for display friendlist
@method_decorator(decorators, name='dispatch')
class FriendView(View):
    template_name = 'premium_user/friend.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        friends_zip, have_friend = showfrndlist(current_user)
        friends_zip = checkPrivacySettings(friends_zip)
        return render(request, self.template_name, {'current_user': friends_zip})

    def post(self, request):
        current_user = request.user
        username1 = current_user.username
        current_user_friendlist, have_friend = showfrndlist(username1)

        for i,j in current_user_friendlist:  
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
                elif request.POST.dict()[selected_user] == "Post on Timeline":
                    request.session['owner'] = selected_user
                    return redirect('premium_user:postcontent')
            except:
                pass

        return HttpResponseRedirect(reverse('premium_user:friend'))

#____________________________________________________Group_____________________________________________________
#function needed in group search 
def request_group(current_user, search_name):
    group_name_list = AddGroup.objects.filter(name__icontains = search_name)
    group_name_list = group_name_list.exclude(admin = current_user.username)

    group_status=[]
    # bundle={}
    bundle=[]
    key = 1
    keyl=[]; groupadminusernamel=[]; groupadminnamel=[];groupnamel = []; statusl=[];grouppricel=[]
    for group in group_name_list: 
        try:
            if current_user.username in group.members:
                group_name = group.name
                group_admin = group.admin        
                group_price = group.price

                user = User.objects.get(username = group_admin)
                name = str(user.first_name)+' '+str(user.last_name)
                keyl.append(key); groupadminusernamel.append(group_admin);groupadminnamel.append(name)
                groupnamel.append(group_name), statusl.append(3), grouppricel.append(group_price)
                key = key+1
               
                #Assumption(group admin cannot formed two group of same name) 
                group_name_list = group_name_list.exclude(admin = group_admin, name = group_name)
        except:
            pass
    
    for group1 in group_name_list:
        try:
            group = GroupRequest.objects.get(admin = group1.admin, name = group1.name)
            
            if current_user.username in group.members:
                #to pass in html
                group_name = group1.name
                group_admin = group1.admin        
                group_price = group1.price

                user = User.objects.get(username = group_admin)
                name = str(user.first_name)+' '+str(user.last_name)
                keyl.append(key); groupadminusernamel.append(group_admin);groupadminnamel.append(name)
                groupnamel.append(group_name), statusl.append(2), grouppricel.append(group_price)
             
                key = key+1
                group_name_list = group_name_list.exclude(admin = group_admin, name = group_name)
        except:
            pass

    for group in group_name_list:  
        group_name = group.name
        group_admin = group.admin        
        group_price = group.price

        user = User.objects.get(username = group_admin)
        name = str(user.first_name)+' '+str(user.last_name)
        keyl.append(key); groupadminusernamel.append(group_admin);groupadminnamel.append(name)
        groupnamel.append(group_name), statusl.append(1), grouppricel.append(group_price)
        key = key+1

    if keyl:
        bundle = zip(keyl, groupadminusernamel, groupadminnamel, groupnamel, statusl, grouppricel)
    return bundle

@method_decorator(decorators, name='dispatch')
class ListGroupView(View):
    template_name = 'premium_user/list_group.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        search_name = findGroup(request).lower()
        bundle = request_group(current_user, search_name)
        if bundle:
            return render(request, self.template_name, {'bundle': bundle})
        else:
            bundle = {}
            return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        username = current_user.username
        search_name = findGroup(request).lower()
        bundle = request_group(current_user, search_name)

        for keyl, groupadminusernamel, groupadminnamel, groupnamel, statusl, grouppricel in bundle:
            try:
                
                if request.POST.dict()[str(keyl)] == "join":
                    print("Button pressed : ", request.POST.dict()[str(keyl)])
                    admin = groupadminusernamel; name = groupnamel

                    wallet = Wallet.objects.get(username=username)
                    amount = wallet.amount; price = grouppricel
                    
                    if ((price <= amount and wallet.transactions_left > 0) or (price == float(0))):
                        if price != float(0):
                            wallet.amount -= price
                            wallet.transactions_left -= 1
                            wallet.save()
                        try:
                            group = GroupRequest.objects.get(admin = admin, name = name)
                            group.members.append(username); group.save()
                            #bundle update
                            statusl = 2
                            # return render(request, self.template_name, {'bundle': bundle})
                            return HttpResponseRedirect(reverse('premium_user:listgroup'))
                        except:
                            group = GroupRequest()
                            group.admin = admin ; group.name = name
                            group.status = 2
                            group.members = [] 
                            group.members.append(username); group.save()
                            #bundle update
                            statusl = 2
                            # return render(request, self.template_name, {'bundle': bundle})
                            return HttpResponseRedirect(reverse('premium_user:listgroup'))
                        
                    else:
                        #message.info NOT WORKING (but not a problem, code working fine)
                        messages.info(request, 'Please recharge.')
                        # return render(request, self.template_name, {'bundle': bundle})
                        return HttpResponseRedirect(reverse('premium_user:listgroup'))

                elif request.POST.dict()[str(keyl)] == "leave":
                    admin = groupadminusernamel; name = groupnamel
                    group = AddGroup.objects.get(admin = admin, name = name)
                    group.members.remove(username)
                    group.save()
                    statusl = 1
                    # return render(request, self.template_name, {'bundle': bundle})
                    return HttpResponseRedirect(reverse('premium_user:listgroup'))
            except:
                pass
        return HttpResponseRedirect(reverse('premium_user:listgroup'))
        # return render(request, self.template_name, {'bundle': bundle})

@method_decorator(decorators, name='dispatch')
class GroupPlanFormView(View):
    form_class = GroupPlanForm
    template_name = 'premium_user/groupplan_form.html'
    
    def get(self, request):
        form = self.form_class(None)
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user
        form = self.form_class(request.POST)
        username = current_user.username

        if form.is_valid():
            plantype = form.cleaned_data['plantype']
            wallet = Wallet.objects.get(username = username)
            amount = wallet.amount

            price, noofgroup = priceofplan(int(plantype))

            if wallet.transactions_left == 0:
                form.add_error('plantype', "You don't have any transactions remaining for the month.")
            else:
                if amount >= price:
                    amount -= price
                    wallet.transactions_left -= 1
                    wallet.amount = amount
                    wallet.save()

                    current_date = datetime.now().date()
                    #Assumption : If user recharge before due date of plan, then numberofgroup + = newplan.numberofgroup
                    try:
                        groupplan = GroupPlan.objects.get(customer = username)
                        groupplan.recharge_on = current_date; groupplan.plantype = plantype
                        groupplan.noofgroup += noofgroup
                        groupplan.save()
                    except:
                        GroupPlan(customer = username, recharge_on = current_date, plantype = plantype, noofgroup = noofgroup).save()
                        
                    name = current_user.first_name + ' ' + current_user.last_name
                    return render(request, 'premium_user/plansuccessfullyopted.html', {'name': name})

                else:
                    form.add_error('plantype', "You don't have sufficient balance.")

        return render(request, self.template_name, {'form': form})


@method_decorator(decorators, name='dispatch')
class AddGroupFormView(View):
    form_class = AddGroupForm
    template_name = 'premium_user/addgroup_form.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        username = current_user.username
        try:
            groupplanofuser = GroupPlan.objects.get(customer = username)
            noofgroup = groupplanofuser.noofgroup
            
            # Recharge validity check
            current_date = datetime.now().date()
            rechargedate = groupplanofuser.recharge_on.now().date()
            days = int((rechargedate - current_date).days)
            if days > 30:
                status = groupplanofuser.plantype
                if status == "1":
                    groupplanofuser.noofgroup = 2
                    groupplanofuser.recharge_on = current_date 
                    groupplanofuser.save()
                elif status == "2":
                    groupplanofuser.noofgroup = 4
                    groupplanofuser.recharge_on = current_date
                    groupplanofuser.save()
                elif status == "3":
                    groupplanofuser.noofgroup = sys.maxsize
                    groupplanofuser.recharge_on = current_date
                    groupplanofuser.save()
                form = self.form_class(None)
                return render(request, self.template_name, {'form': form})

            if noofgroup > 0:
                #blank form added
                form = self.form_class(None)
                return render(request, self.template_name, {'form': form})

            else:
                name = current_user.first_name + ' ' + current_user.last_name
                bundle = dict(); errortype = 1
                bundle[errortype] = name
                return render(request, 'premium_user/error.html', {'bundle': bundle})
        except:
            name = current_user.first_name + ' ' + current_user.last_name
            bundle = dict(); errortype = 0
            bundle[errortype] = name
            return render(request, 'premium_user/error.html', {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        username = current_user.username
        form = self.form_class(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            gtype = form.cleaned_data['gtype']
            price = form.cleaned_data['price']
            if not price:
                price = 0
            if price < 0:
                form.add_error('price', "Only allowed positive number.")
                return render(request, self.template_name, {'form': form})
            if price <= 0 and gtype == '2':
                form.add_error('price', "Have to put some amount for creating commercial group.")
                return render(request, self.template_name, {'form': form})
                
            try:
                group= Group.objects.get(admin = current_user.username)
                grouplist = group.group_list
                if name in grouplist:
                    form.add_error('name', "Group name already exist, Enter different group name.")
                    return render(request, self.template_name, {'form': form})
            except:
                pass
            if int(gtype) == 1:
                price = 0
            addgroup = AddGroup(admin=current_user.username, name=name, gtype=gtype, price=price)
            addgroup.members = []
            addgroup.members.append(current_user.username)
            addgroup.save()
            groupplan = GroupPlan.objects.get(customer = username)
            groupplan.noofgroup -=1
            groupplan.save()
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
            
        return HttpResponseRedirect(reverse('premium_user:groupdetails'))
    

def return_bundle_for_request(current_user):
    current_request = GroupRequest.objects.filter(admin = current_user.username)
    key = 1
    bundle = {}
    group_request = []
    for i in current_request:
        gname = i.name
        for member in i.members:
            userObj = User.objects.get(username = member)
            name = str(userObj.first_name) + ' ' + str(userObj.last_name)  
            temp={}; temp[gname] = member
            temp1={}; temp1[name] = temp
            bundle[key] = temp1

            group_request.append([key, gname, member, name])
            key = key + 1
            
    return bundle, group_request

@method_decorator(decorators, name='dispatch')
class ListRequestView(View):
    template_name = 'premium_user/listrequest.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
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

                    group = GroupRequest.objects.get(admin = admin, name = name)
                    group.members.remove(member); group.save()
                    add_group = AddGroup.objects.get(admin = admin, name = name)
                    add_group.members.append(member); add_group.save()
                    break
                       
                elif request.POST.dict()[str(value[0])] == "reject":

                    name = value[1]; member = value[2]
                    admin = current_user.username
                    group = GroupRequest.objects.get(admin = admin, name = name)
                    group.members.remove(member); group.save()

                    add_group = AddGroup.objects.get(admin = admin, name = name)

                    #if user request reject revert the money back 
                    wallet = Wallet.objects.get(username=member)
                    wallet.amount += add_group.price
                    wallet.transactions_left += 1
                    wallet.save()
                    break
            except:
                pass

        bundle, group_request = return_bundle_for_request(current_user)
        return render(request, self.template_name, {'bundle': bundle})

def listowngroup(current_user):
    try:
        owngroup = Group.objects.get(admin = current_user.username)
        allowngroup = []
        for group in owngroup.group_list:
            allowngroup.append(group)
    except:
        allowngroup = []
    return allowngroup

@method_decorator(decorators, name='dispatch')
class DeleteGroupView(View):
    template_name = 'premium_user/deletegroup.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        bundle = listowngroup(current_user)
        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        bundle = listowngroup(current_user)

        for group in bundle:
            try:
                if request.POST.dict()[str(group)] == "Delete":
                    groupobj = Group.objects.get(admin = current_user.username)
                    groupobj.group_list.remove(group); groupobj.save()
                    addgroupObj = AddGroup.objects.get(admin = current_user.username, name = group)
                    addgroupObj.delete()
                    
                    groupplan = GroupPlan.objects.get(customer = current_user.username)
                    groupplan.noofgroup += 1
                    groupplan.save()

                    break
            except:
                pass

        bundle = listowngroup(current_user)
        return render(request, self.template_name, {'bundle': bundle})

def listjoinedgroup(current_user):
    addgroup = AddGroup.objects.all()
    groupname = []; adusername = []; adname = []; price = []; gmembers = []; key=[]
    uname = current_user.username
    bundle = []; count = 1
    for i in addgroup:
        if uname in list(i.members):
            if i.admin != uname:
                groupname.append(i.name); adusername.append(i.admin)
                userObj = User.objects.get(username = i.admin)
                name = str(userObj.first_name) + ' ' + (userObj.last_name)
                adname.append(name); price.append(i.price)
                members = ""
                for m in list(i.members):
                    newuserObj = User.objects.get(username = m)
                    name = str(newuserObj.first_name) + ' ' + (newuserObj.last_name)
                    members = members + " '"+name+"' "
                gmembers.append(members)
                key.append(count)
                count += 1

    if count > 1:
        bundle = zip(key, adusername, adname, groupname, price, gmembers)
    else:
        bundle =[]
    return bundle

@method_decorator(decorators, name='dispatch')
class JoinedGroupView(View):
    template_name = 'premium_user/yourjoinedgroup.html'
    
    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        bundle = listjoinedgroup(current_user)
        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        bundle = listjoinedgroup(current_user)
        for key, adusername, adname, groupname, price, gmembers in bundle:
            try:
                if request.POST.dict()[str(key)] == "leave":
                    group = AddGroup.objects.get(admin = adusername, name = groupname)
                    group.members.remove(current_user.username)
                    group.save()
            except:
                pass
        return HttpResponseRedirect(reverse('premium_user:yourjoinedgroup'))
#______________________________________________________ wallet_____________________________________________

@method_decorator(decorators, name='dispatch')
class WalletView(View):
    template_name = 'premium_user/mywallet.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        wallet = Wallet.objects.get(username = current_user.username)

        w_dict = dict() 

        w_dict['Account Type'] = wallet.user_type
        w_dict['Amount'] = wallet.amount
        w_dict['Remaining Transactions'] = wallet.transactions_left
        
        return render(request, self.template_name, {'wallet': w_dict})

def generateOTP():
    current_date_time = str(datetime.now())
    data_encode = current_date_time.encode('utf-8').strip()
    hash_obj = hashlib.sha256()
    hash_obj.update(data_encode)
    hash_value = hash_obj.hexdigest()

    i = 0
    a = 0; b = 0; c = 0; d = 0

    for j in range(4, len(hash_value)+1, 4):
        hash_split = hash_value[i:j]
        a = (a + int(hash_split[0], 16))%10
        b = (b + int(hash_split[1], 16))%10
        c = (c + int(hash_split[2], 16))%10
        d = (d + int(hash_split[3], 16))%10
        i = j
    otp = str(a) + str(b) + str(c) + str(d)
    return otp

def sendOTP(request, email, subject):
    otp = generateOTP()

    message = 'The one-time password for this transaction is: ' + otp + '. This otp is valid for 180 seconds only. Please enter the code for completing this transaction.'

    # vulnerable!
    request.session['otp'] = otp

    curr_time = time.time()

    request.session['timer'] = str(curr_time)

    c = send_mail(
        subject,
        message,
        'admin@socialnet.com',
        [email],
        fail_silently=False,
    )

    return c

@method_decorator(decorators, name='dispatch')
class AddMoneyFormView(View):
    form_class = AddMoneyForm
    template_name = 'premium_user/addmoney.html'

    def get(self, request):
        form = self.form_class(None)
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        current_user = request.user

        if form.is_valid():
            amount = form.cleaned_data['amount']
            username = current_user.username

            # Implement OTP functionality here

            email = User.objects.get(username=username).email
            subject = 'OTP for Add Money Transaction'
            c = sendOTP(request, email, subject)

            if c==1:
                wallet = Wallet.objects.get(username=username)
                if wallet.transactions_left == 0:
                    form.add_error('amount', "You don't have any transactions remaining for the month.")
                else:
                    request.session['trans_type'] = 'add'
                    request.session['amount'] = str(amount)
                    return redirect('premium_user:otpverify')
            else:
                form.add_error('amount', 'OTP generation failed. Please check your network connection.') 

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'premium_user/sendmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        friend_list = None
        try:
            friend_list = Friend.objects.get(username=request.user).friend_list
        except:
            friend_list = []
        if len(friend_list) > 0:
            return render(request, self.template_name, {'form': form})
        else:
            return redirect('premium_user:nofriends')
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            send_to = form.cleaned_data['send_to']
            username = current_user.username
            sender_wallet = Wallet.objects.get(username=current_user)

            if sender_wallet.transactions_left == 0:
                form.add_error('amount', "You don't have any transactions remaining for the month.")
            elif float(amount) > sender_wallet.amount:
                form.add_error('amount', "You don't have enough balance.")
            elif float(amount) == 0:
                form.add_error('amount', "Enter amount greater than 0.")
            else:
                email = User.objects.get(username=username).email
                subject = 'OTP for Send Money Transaction'
                c = sendOTP(request, email, subject)

                if c==1:
                    request.session['trans_type'] = 'send'
                    request.session['amount'] = str(amount)
                    request.session['send_to'] = send_to
                    return redirect('premium_user:otpverify')
                else:          
                    form.add_error('amount', 'OTP generation failed. Please check your network connection.')

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'premium_user/requestmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        friend_list = None
        try:
            friend_list = Friend.objects.get(username=request.user).friend_list
        except:
            friend_list = []
        if len(friend_list) > 0:
            return render(request, self.template_name, {'form': form})
        else:
            return redirect('premium_user:nofriends')

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            request_from = form.cleaned_data['request_from']
            username = current_user.username

            # Implement OTP functionality here

            email = User.objects.get(username=username).email
            subject = 'OTP for Send Money Transaction'
            c = sendOTP(request, email, subject)

            if c==1:

                sender = Wallet.objects.get(username=current_user)

                if sender.transactions_left == 0:
                    form.add_error('amount', "You don't have any transactions remaining for the month.")
                else:
                    # check number of pending requests made
                    pending_requests = len(Request.objects.filter(sender=current_user, status=0))
                    
                    if sender.transactions_left - pending_requests > 0:
                        request.session['trans_type'] = 'req'
                        request.session['amount'] = str(amount)
                        request.session['request_from'] = request_from
                        return redirect('premium_user:otpverify')
                    else:
                        form.add_error('amount', "You have transactions pending. Can't request at this point.")
            else:
                form.add_error('amount', 'OTP generation failed. Please check your network connection.')

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class PendingRequestsView(View):
    template_name = 'premium_user/pendingrequests.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        pay_requests = Request.objects.filter(receiver=current_user, status=0)
        bundle = dict()
        bundle['requests'] = pay_requests
        return render(request, self.template_name, {'pay_req': bundle})

    def post(self, request):
        current_user = request.user
        all_requests = Request.objects.filter(receiver=current_user, status=0)

        for req in all_requests:
            if request.POST.dict().get(req.request_id) is not None:
                curr_request = Request.objects.get(request_id=req.request_id)
                if request.POST.dict()[req.request_id] == "Pay":
                    sender_wallet = Wallet.objects.get(username=current_user)
                    receiver_wallet = Wallet.objects.get(username=req.sender)
                    if sender_wallet.amount >= req.amount and receiver_wallet.transactions_left > 0:
                        sender_wallet.amount -= req.amount
                        receiver_wallet.amount += req.amount
                        receiver_wallet.transactions_left -= 1
                        sender_wallet.save()
                        receiver_wallet.save()
                        curr_request.status = 1
                        curr_request.save()
                        Transaction(sender=current_user, receiver=req.sender, amount=req.amount, timestamp=timezone.now()).save()
                    else:
                        # If requested amount is greater than current balance, the request is dropped.
                        curr_request.status = 2
                        curr_request.save()
                elif request.POST.dict()[req.request_id] == "Decline":
                    curr_request.status = 2
                    curr_request.save()

        return HttpResponseRedirect(reverse('premium_user:pendingrequests'))


@method_decorator(decorators, name='dispatch')
class OTPVerificationFormView(View):
    form_class = OTPVerificationForm
    template_name = 'premium_user/otpverify.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user

        form = self.form_class(request.POST)
        current_date = datetime.now().date()
        if form.is_valid():
            otp = form.cleaned_data['otp']

            try:
                if request.session['otp'] != otp:
                    form.add_error('otp', 'Wrong OTP entered!')
                elif time.time() > float(request.session['timer']) + 180:
                    form.add_error('otp', 'Timer expired!')
                else: 
                    request.session.pop('otp', None)
                    request.session.pop('timer', None)
                    request.session.modified = True

                    flag = False

                    try:
                        plan = request.session['plan']
                        t_amount = 50
                        if  plan == "1":
                            amount = float(request.session['sub_amount'])
                            amount = amount - 50
                            GroupPlan(customer = current_user.username, recharge_on = current_date, plantype = plan, noofgroup = 2).save()
                            t_amount = 50
                            # Add no. of groups the user can create here
                            flag = True
                        elif plan == "2":
                            amount = float(request.session['sub_amount'])
                            amount = amount - 100
                            GroupPlan(customer = current_user.username, recharge_on = current_date, plantype = plan, noofgroup = 4).save()
                            t_amount = 100
                            # Add no. of groups the user can create here
                            flag = True
                        elif plan == "3":
                            amount = float(request.session['sub_amount'])
                            amount = amount - 150
                            GroupPlan(customer = current_user.username, recharge_on = current_date, plantype = plan, noofgroup = sys.maxsize).save()
                            t_amount = 150
                            # Add no. of groups the user can create here
                            flag = True
                        else:
                            form.add_error('otp', 'Unknown transaction!')

                        if flag:
                            wallet = Wallet.objects.get(username=str(current_user))
                            wallet.amount = amount
                            wallet.save()

                            Transaction(sender=str(current_user), receiver='Admin', amount=t_amount, timestamp=timezone.now()).save()
                            if amount > 0:
                                Transaction(sender=str(current_user), receiver=str(current_user), amount=amount, timestamp=timezone.now()).save()

                            p_user = PremiumUser.objects.get(user=current_user)
                            p_user.subscription = int(plan)
                            p_user.save()

                            request.session.pop('plan', None)
                            request.session.pop('sub_amount', None)
                            request.session.modified = True

                            return HttpResponseRedirect(reverse('premium_user:homepage'))
                    except:
                        if request.session['trans_type'] == 'add':
                            request.session.pop('trans_type', None)
                            request.session.modified = True
                            username = current_user.username
                            wallet = Wallet.objects.get(username=username)
                            wallet.amount += float(request.session['amount'])
                            wallet.transactions_left -= 1
                            wallet.save()

                            # Add to Transactions table
                            Transaction(sender=username, receiver=username, amount=float(request.session['amount']), timestamp=timezone.now()).save()

                            request.session.pop('amount', None)
                            request.session.modified = True

                            w_dict = dict() 

                            w_dict['Account Type'] = wallet.user_type
                            w_dict['Amount'] = wallet.amount
                            w_dict['Remaining Transactions'] = wallet.transactions_left

                            return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})

                        elif request.session['trans_type'] == 'send':
                            request.session.pop('trans_type', None)
                            request.session.modified = True

                            sender_wallet = Wallet.objects.get(username=current_user)
                            receiver_wallet = Wallet.objects.get(username=request.session['send_to'])

                            sender_wallet.amount -= float(request.session['amount'])
                            sender_wallet.transactions_left -= 1    # Assumption: Sending money causes one transaction of the sender to be exhausted.
                            receiver_wallet.amount += float(request.session['amount'])
                            sender_wallet.save()
                            receiver_wallet.save()

                            # Add to Transactions table
                            Transaction(sender=current_user, receiver=request.session['send_to'], amount=float(request.session['amount']), timestamp=timezone.now()).save()

                            request.session.pop('amount', None)
                            request.session.pop('send_to', None)
                            request.session.modified = True

                            w_dict = dict() 

                            w_dict['Account Type'] = sender_wallet.user_type
                            w_dict['Amount'] = sender_wallet.amount
                            w_dict['Remaining Transactions'] = sender_wallet.transactions_left

                            return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})

                        elif request.session['trans_type'] == 'req':
                            request.session.pop('trans_type', None)
                            request.session.modified = True

                            sender = Wallet.objects.get(username=current_user)

                            # Add entry to Request table
                            req_count = len(Request.objects.all())
                            req_id = "RQST-" + str(req_count + 1)
                            Request(request_id=req_id, sender=current_user, receiver=request.session['request_from'], amount=float(request.session['amount']), status=0).save()

                            request.session.pop('amount', None)
                            request.session.pop('request_from', None)
                            request.session.modified = True

                            # Assumption: If the request is accepted, then no. of transactions is deducted by one.

                            w_dict = dict()

                            w_dict['Account Type'] = sender.user_type
                            w_dict['Amount'] = sender.amount
                            w_dict['Remaining Transactions'] = sender.transactions_left

                            return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})

                        else:
                            form.add_error('otp', 'Unknown transaction!')
            except:
                form.add_error('otp', 'Unauthorised transaction!')

        return render(request, self.template_name, {'form': form})

#_________________________________________________Message______________________________________________________
def getfriendlist(username1):
    try:
        have_friend = Friend.objects.get(username = username1)
        friendlist  = list(have_friend.friend_list)
    except:
        friendlist = []
    return friendlist

def saveMessage(self, request, sender, receiver):
    search_msg = request.POST.dict()['messagearea']
    # call below function to decrypt(after package install)

    try:
        search_msg =  decryptcipher(current_user, search_msg) 
    except:
        Print("ERROR IN PKI")
        pass

    if search_msg:
        getmessage = search_msg
        search_msg = ""
        time_stamp = timezone.now()
        userObj = User.objects.get(username = sender)
        sendername = str(userObj.first_name) + ' ' + str(userObj.last_name)
        update_message = "From " + str(sendername)+" : "+ str(getmessage) + '\n'+ 'At : '+ str(time_stamp)
        try:
            user_message = Message.objects.get(sender = sender, receiver = receiver)
            user_message.messages.append(update_message)
            user_message.timestamp.append(time_stamp)
            user_message.save()
        except:
            Message(sender = sender, receiver = receiver, messages = [update_message], timestamp = [time_stamp]).save()

class Saveuser:
    username = ""
usernameObj = Saveuser() 


@method_decorator(decorators, name='dispatch')
class InboxView(View):
    template_name = 'premium_user/inbox.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        username1 = current_user.username
        friendlist = getfriendlist(username1)
        current_user = dict()
            
        userinfo=dict()
        if friendlist:
            uname = []
            for i in friendlist:
                userObj = User.objects.get(username = i)
                name = str(userObj.first_name) + ' ' + str(userObj.last_name)
                uname.append(name)
            info = zip(friendlist, uname)
            userinfo[username1] = info
        else:
            userinfo = dict()
        return render(request, self.template_name, {'userinfo': userinfo})

    def post(self, request):
        current_user = request.user
        username1 = current_user.username
        friendlist = getfriendlist(username1)
        
        for i in friendlist:
            try:
                selected_user = i
                if request.POST.dict()[selected_user] == "Send Message":
                    usernameObj.username = ""
                    usernameObj.username = selected_user
            except:
                pass
        return redirect('premium_user:chat')

def showmessages(sender, receiver):
    count = 0
    try:
        messagebundle1 = Message.objects.get(sender = sender, receiver = receiver)
        messages1 = list(messagebundle1.messages);  timestamp1 = list(messagebundle1.timestamp)
    except:
        messages1 = []; timestamp1 = []; count += 1
        pass
    try:
        messagebundle2 = Message.objects.get(sender = receiver, receiver = sender)
        messages2 = list(messagebundle2.messages); timestamp2 = list(messagebundle2.timestamp)
        
    except:
        messages2 = []; timestamp2 = []
        count += 1
        pass
    if count != 2:
        messages = messages1 + messages2
        timestamp = timestamp1 + timestamp2
        updatemessages = [x for _,x in sorted(zip(timestamp,messages), reverse= True)]
    else:
        updatemessages =  []
    return updatemessages

@method_decorator(decorators, name='dispatch')
class ChatView(View):
    template_name = 'premium_user/chat.html'

    def get(self, request):
        current_user = request.user
        if PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        sender = current_user.username
        receiver = usernameObj.username
        updatemessages = showmessages(sender, receiver)
        msg = {'updatemessages':updatemessages}
        return render(request, self.template_name, {'msg': msg})

    def post(self, request):
        current_user = request.user
        sender = current_user.username
        receiver = usernameObj.username
        saveMessage(self, request, sender, receiver)
        return HttpResponseRedirect(reverse('premium_user:chat'))

@method_decorator(decorators, name='dispatch')
class PostContentView(View):
    template_name = 'premium_user/postcontent.html'

    def get(self, request):
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        owner = request.session.get('owner')
        owner = User.objects.get(username=owner).first_name + " " + User.objects.get(username=owner).last_name
        visitor = request.user
        visitor = User.objects.get(username=visitor).first_name + " " + User.objects.get(username=visitor).last_name
        return render(request, self.template_name, {'owner':owner, 'visitor':visitor})

    def post(self, request):
        owner = request.session.get('owner')
        visitor = request.user
        savePost(request, owner, visitor)
        request.session.pop('owner', None)
        request.session.modified = True
        return redirect('premium_user:friend')

@method_decorator(decorators, name='dispatch')
class NofriendsView(View):
    template_name = 'premium_user/nofriends.html'

    def get(self, request):
        if PremiumUser.objects.get(user=request.user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        return render(request, self.template_name)

@method_decorator(decorators, name='dispatch')
class SettingsView(View):
    template_name = 'premium_user/settings.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        elif PremiumUser.objects.get(user=current_user).subscription == 0:
            return HttpResponseRedirect(reverse('premium_user:subscription'))
        else:
            level = Timeline.objects.get(username=current_user).level
            if level:
                level = "Friends"
            else:
                level = "Only Me"
            return render(request, self.template_name, {'level': level})

    def post(self, request):
        current_user = request.user
        scope = request.POST.dict()['level']
        user_timeline = Timeline.objects.get(username=str(current_user))

        if scope == "0":
            user_timeline.level = 0
        elif scope == "1":
            user_timeline.level = 1
        
        user_timeline.save()
        return HttpResponseRedirect(reverse('premium_user:settings'))

class SubscriptionFormView(View):
    form_class = SubscriptionForm
    template_name = 'premium_user/subscriptionform.html'

    def get(self, request):
        current_user = request.user
        form = self.form_class(None)
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            p_user = PremiumUser.objects.get(user=current_user)
        
            if p_user.subscription > 0:
                return HttpResponseRedirect(reverse('premium_user:homepage'))
            else:
                return render(request, self.template_name, {'form':form})
        
    def post(self, request):
        current_user = request.user
        form = self.form_class(request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            plan = form.cleaned_data['subscription_plan']
            
            if plan == "2" and amount < 100:
                form.add_error('amount', 'Enter amount greater than Rs. 100')
            elif plan == "3" and amount < 150:
                form.add_error('amount', 'Enter amount greater than Rs. 150')
            else:
                email = User.objects.get(username=str(current_user)).email
                subject = 'OTP for Subscription Payment'
                c = sendOTP(request, email, subject)

                if c == 1:
                    request.session['sub_amount'] = str(amount)
                    request.session['plan'] = plan
                    return HttpResponseRedirect(reverse('premium_user:otpverify'))
                else:
                    form.add_error('amount', 'OTP generation failed. Please check your network connection.')    
            
        return render(request, self.template_name, {'form':form})
        

@method_decorator(decorators, name='dispatch')
class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('login:login'))

