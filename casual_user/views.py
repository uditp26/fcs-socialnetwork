from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404
from .models import CasualUser, Post, Friend, Wallet, Request, Transaction
from login.models import User
from premium_user.models import AddGroup, GroupRequest

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from .forms import AddMoneyForm, SendMoneyForm, RequestMoneyForm, EditProfileForm, OTPVerificationForm

from datetime import datetime

import time
from django.core.mail import send_mail
import hashlib

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

decorators = [cache_control(no_cache=True, must_revalidate=True, no_store=True), login_required(login_url='https://127.0.0.1:8000/login/')]

def savePost(self, request, current_user):

    post = request.POST.dict()['postarea']
    scope = request.POST.dict()['level']

    timestamp = datetime.now(tz=None)
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
    casual_user = CasualUser.objects.get(user=current_user)
    bundle = dict()
    name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
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

def updateExistingUser(curr_user, first_name, last_name, gender, phone):
    
    curr_user.first_name = first_name
    curr_user.last_name = last_name
    curr_user.save()
    curr_user = CasualUser.objects.get(user=curr_user)
    curr_user.gender = gender
    curr_user.phone = phone
    curr_user.save()

@method_decorator(decorators, name='dispatch')
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
        return HttpResponseRedirect('')

@method_decorator(decorators, name='dispatch')
class ProfileView(View):
    template_name = 'casual_user/myprofile.html'

    def get(self, request):
        current_user = request.user

        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CasualUser.objects.get(user=current_user)
            bundle = dict()
            #name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            fname = casual_user.user.first_name
            lname = casual_user.user.last_name
            gender = casual_user.gender
            if gender==1:
                gender = str("Male")
            elif gender==2:
                gender = str("Female")
            elif gender==3:
                gender = str("Transgender")
            bundle = {'First Name': fname, 'Last Name': lname,'Date of Birth': casual_user.date_of_birth, 'Gender': gender, 'Email':casual_user.email, 'Phone': casual_user.phone}
            return render(request, self.template_name, {'current_user':bundle})

@method_decorator(decorators, name='dispatch')
class EditProfileFormView(View):
    form_class = EditProfileForm
    template_name = 'casual_user/editprofile.html'
    
    def get(self, request):
        current_user = request.user
        print(type(current_user))
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CasualUser.objects.get(user=current_user)
            bundle = dict()
            #name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            fname = casual_user.user.first_name
            lname = casual_user.user.last_name
            gender = casual_user.gender
            if gender==1:
                gender = str("Male")
            elif gender==2:
                gender = str("Female")
            elif gender==3:
                gender = str("Transgender")
            bundle = {'first_name': fname, 'last_name': lname, 'gender': gender, 'phone': casual_user.phone}
            return render(request, self.template_name, {'current_user':bundle})

    def post(self, request):
        current_user = request.user

        first_name = request.POST.dict()['first_name']
        last_name = request.POST.dict()['last_name']
        gender = request.POST.dict()['gender']
        phone = request.POST.dict()['phone']
        gender_string = gender
        if gender=="Male":
            gender = 1
        elif gender=="Female":
            gender = 2
        elif gender=="Transgender":
            gender = 3
        updateExistingUser(current_user, first_name, last_name, gender, phone)
        return HttpResponseRedirect('')


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
        have_friend = Friend()
        have_friend.username = username1
        current_user_friendlist = []
        have_friend.friend_list = current_user_friendlist

    search_name = findfriend(request).lower()

    print("search name : ", search_name)

    user_name_list = User.objects.filter(first_name__icontains = search_name)

    user_name_list = user_name_list.exclude(username = current_user.username)

    return user_name_list, current_user_friendlist, have_friend


@method_decorator(decorators, name='dispatch')
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

                    # check if any pending money requests between the users; if yes, delete the requests.

                    Request.objects.filter(sender=selected_user, receiver=have_friend.username).delete()
                    Request.objects.filter(sender=have_friend.username, receiver=selected_user).delete()

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

def showfrndlist(username1):
    try:
        have_friend = Friend.objects.get(username=username1)
        current_user_friendlist = list(have_friend.friend_list)
    except:
        current_user_friendlist = []

    return have_friend, current_user_friendlist

#for display friendlist
@method_decorator(decorators, name='dispatch')
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

        have_friend, current_user_friendlist = showfrndlist(username1)

        for i in current_user_friendlist:
            print(request.POST.dict())
            try:
                selected_user = i

                if request.POST.dict()[selected_user] == "Unfriend":
                    
                    # check if any pending money requests between the users; if yes, delete the requests.

                    Request.objects.filter(sender=selected_user, receiver=have_friend.username).delete()
                    Request.objects.filter(sender=have_friend.username, receiver=selected_user).delete()

                    have_friend.friend_list.remove(selected_user)
                    have_friend.save()

                    #for implementation of bi-direction remove_friend
                    b_user_friendlist = Friend.objects.get(username = selected_user)
                    b_user_friendlist.friend_list.remove(current_user.username)
                    b_user_friendlist.save()

                    break
            except:
                pass

        have_friend, current_user_friendlist = showfrndlist(username1)

        current_user = dict()
        current_user[username1] = current_user_friendlist

        return render(request, self.template_name, {'current_user': current_user})

@method_decorator(decorators, name='dispatch')
class WalletView(View):
    template_name = 'casual_user/mywallet.html'

    def get(self, request):
        current_user = request.user
        wallet = Wallet.objects.get(username=current_user.username)

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
    template_name = 'casual_user/addmoney.html'

    def get(self, request):
        form = self.form_class(None)
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

            if c == 1:
                wallet = Wallet.objects.get(username=username)
                if wallet.transactions_left == 0:
                    form.add_error('amount', "You don't have any transactions remaining for the month.")
                else:
                    request.session['trans_type'] = 'add'
                    request.session['amount'] = str(amount)
                    return redirect('casual_user:otpverify')
            else:
                form.add_error('amount', 'OTP generation failed. Please check your network connection.')

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'casual_user/sendmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        friend_list = None
        try:
            friend_list = Friend.objects.get(username=request.user).friend_list
        except:
            friend_list = []
        if len(friend_list) > 0:
            return render(request, self.template_name, {'form': form})
        else:
            return redirect('casual_user:nofriends')
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
                    return redirect('casual_user:otpverify')
                else:          
                    form.add_error('amount', 'OTP generation failed. Please check your network connection.')

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'casual_user/requestmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        friend_list = None
        try:
            friend_list = Friend.objects.get(username=request.user).friend_list
        except:
            friend_list = []
        if len(friend_list) > 0:
            return render(request, self.template_name, {'form': form})
        else:
            return redirect('casual_user:nofriends')

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
                        return redirect('casual_user:otpverify')
                    else:
                        form.add_error('amount', "You have transactions pending. Can't request at this point.")
            else:
                form.add_error('amount', 'OTP generation failed. Please check your network connection.')

        return render(request, self.template_name, {'form': form})

#___________________________________________________________________________________________________        

def request_bundle(current_user, search_name):
    group_name_list = AddGroup.objects.filter(name__icontains = search_name)
    group_name_list = group_name_list.exclude(admin = current_user.username)

    group_status=[]
    bundle={}
    
    key = 1
    for group in group_name_list:
        try:
            if current_user.username in group.members:
                #to store as backup
                group_name = group.name
                group_admin = group.admin
                group_status.append([key, group_admin, group_name, 3])
                
                #to pass in html
                temp={}
                temp[group_name] = 3
                bundle[key] = temp
                key = key+1
                #Assumption(group admin cannot formed two group of same name) 
                group_name_list = group_name_list.exclude(admin = group_admin, name = group_name)
        except:
            pass
    
    for group in group_name_list:
        try:
            group = GroupRequest.objects.get(admin = group.admin, name = group.name)
            
            if current_user.username in group.members:
                group_name = group.name
                group_admin = group.admin                 
                group_status.append([key, group_admin, group_name, 2])
                
                #to pass in html
                temp={}
                temp[group_name] = 2
                bundle[key] = temp
                key = key+1
                group_name_list = group_name_list.exclude(admin = group_admin, name = group_name)
        except:
            pass

    for group in group_name_list:
        group_name = group.name
        group_admin = group.admin
        group_status.append([key, group_admin, group_name, 1])
                
        temp={}
        temp[group_name] = 1
        bundle[key] = temp

        key = key+1

    return bundle, group_status
#________________________________________________________________________________________________________________
@method_decorator(decorators, name='dispatch')
class ListGroupView(View):
    template_name = 'casual_user/list_group.html'
    
    def get(self, request):
        current_user = request.user
        
        search_name = findGroup(request).lower()
        # print("search name : ", search_name)
        bundle , group_status = request_bundle(current_user, search_name)
        return render(request, self.template_name, {'bundle': bundle})

    def post(self, request):
        current_user = request.user
        username = current_user.username

        search_name = findGroup(request).lower()
        # print("search name : ", search_name)

        bundle , group_status = request_bundle(current_user, search_name)
        
        print("Previous Bundle : ", bundle)

        for value in group_status:
            print(request.POST.dict())
            try:
                if request.POST.dict()[str(value[0])] == "join":
                    admin = value[1]; name = value[2]
                    try:
                        group = GroupRequest.objects.get(admin = admin, name = name)
                        group.members.append(username)
                        group.save()
                        #bundle update
                        bundle[value[0]][name] = 2
                        break
                    except:
                        group = GroupRequest()
                        group.admin = admin ; group.name = name
                        group.status = 2
                        group.members = [] 
                        group.members.append(username)
                        group.save()
                        #bundle update
                        bundle[value[0]][name] = 2
                        break
                
                elif request.POST.dict()[str(value[0])] == "leave":
                    admin = value[1]; name = value[2]
                    group = AddGroup.objects.get(admin = admin, name = name)
                    group.members.remove(username)
                    group.save()

                    bundle[value[0]][name] = 1
                    break

            except:
                pass
        
        print("Modified Bundle :", bundle)
        return render(request, self.template_name, {'bundle': bundle})
        
@method_decorator(decorators, name='dispatch')
class PendingRequestsView(View):
    template_name = 'casual_user/pendingrequests.html'

    def get(self, request):
        current_user = request.user
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
                        Transaction(sender=current_user, receiver=req.sender, amount=req.amount, timestamp=datetime.now(tz=None)).save()
                    else:
                        # If requested amount is greater than current balance, the request is dropped.
                        curr_request.status = 2
                        curr_request.save()
                elif request.POST.dict()[req.request_id] == "Decline":
                    curr_request.status = 2
                    curr_request.save()

        # pay_requests = Request.objects.filter(receiver=current_user, status=0)
        # bundle = dict()
        # bundle['requests'] = pay_requests
        # return render(request, self.template_name, {'pay_req': bundle})
        return HttpResponseRedirect('')

@method_decorator(decorators, name='dispatch')
class OTPVerificationFormView(View):
    form_class = OTPVerificationForm
    template_name = 'casual_user/otpverify.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user

        form = self.form_class(request.POST)

        if form.is_valid():
            otp = form.cleaned_data['otp']

            if request.session['otp'] != otp:
                form.add_error('otp', 'Wrong OTP entered!')
            elif time.time() > float(request.session['timer']) + 180:
                form.add_error('otp', 'Timer expired!')
            else: 
                request.session.pop('otp', None)
                request.session.pop('timer', None)
                request.session.modified = True

                if request.session['trans_type'] == 'add':
                    request.session.pop('trans_type', None)
                    request.session.modified = True
                    username = current_user.username
                    wallet = Wallet.objects.get(username=username)
                    wallet.amount += float(request.session['amount'])
                    wallet.transactions_left -= 1
                    wallet.save()

                    # Add to Transactions table
                    Transaction(sender=username, receiver=username, amount=float(request.session['amount']), timestamp=datetime.now(tz=None)).save()

                    request.session.pop('amount', None)
                    request.session.modified = True

                    w_dict = dict() 

                    w_dict['Account Type'] = wallet.user_type
                    w_dict['Amount'] = wallet.amount
                    w_dict['Remaining Transactions'] = wallet.transactions_left

                    return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})

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
                    Transaction(sender=current_user, receiver=request.session['send_to'], amount=float(request.session['amount']), timestamp=datetime.now(tz=None)).save()

                    request.session.pop('amount', None)
                    request.session.pop('send_to', None)
                    request.session.modified = True

                    w_dict = dict() 

                    w_dict['Account Type'] = sender_wallet.user_type
                    w_dict['Amount'] = sender_wallet.amount
                    w_dict['Remaining Transactions'] = sender_wallet.transactions_left

                    return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})

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

                    return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})

                else:
                    form.add_error('otp', 'Unknown transaction!')
                

        return render(request, self.template_name, {'form': form})

@method_decorator(decorators, name='dispatch')
class NofriendsView(View):
    template_name = 'casual_user/nofriends.html'

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(decorators, name='dispatch')
class LogoutView(View):
    template_name = 'login/login.html'

    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))

