from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from .models import CasualUser, Post, Friend, Wallet, Request, Transaction, FriendRequest
from login.models import User
from premium_user.models import AddGroup, GroupRequest, PremiumUser, Message, Group

from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from .forms import AddMoneyForm, SendMoneyForm, RequestMoneyForm, EditProfileForm
from datetime import datetime

def get_user_info(current_user):
    try:
        login_user = CasualUser.objects.get(user=current_user)
    except:
        pass
    try:
        login_user = PremiumUser.objects.get(user=current_user)
    except:
        pass
    return login_user

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
    login_user = get_user_info(current_user)
    bundle = dict()
    name = login_user.user.first_name + ' ' +  login_user.user.last_name
    user_posts = Post.objects.filter(username=str(current_user))
    # use post 'level' information
    all_posts = None

    pposts = []

    if len(user_posts) > 0:
        pposts = list(reversed(user_posts[0].private_posts))
        pposts += list(reversed(user_posts[0].friends_posts))   # reverses the list

    # fetch friends' posts

    f_user = Friend.objects.filter(username = str(current_user))

    f_posts = []

    if len(f_user) > 0:

        friends = f_user[0].friend_list

        for frnd in friends:
            fp = Post.objects.filter(username=frnd)

            if len(fp) > 0:
                f_posts += list(reversed(fp[0].friends_posts))

    all_posts = pposts + f_posts

    bundle = {'name': name, 'posts':all_posts}
    return bundle

def updateExistingUser(curr_user, first_name, last_name, gender, phone):
    curr_user.first_name = first_name
    curr_user.last_name = last_name
    curr_user.save()
    try:
        curr_user = CasualUser.objects.get(user=curr_user)
    except:
        pass
    try:
        curr_user = PremiumUser.objects.get(user=curr_user)
    except:
        pass
    curr_user.gender = gender
    curr_user.phone = phone
    curr_user.save()

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


class EditProfileFormView(View):
    form_class = EditProfileForm
    template_name = 'casual_user/editprofile.html'
    
    def get(self, request):
        current_user = request.user
        print(type(current_user))
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            login_user = get_user_info(current_user)
            fname = login_user.user.first_name
            lname = login_user.user.last_name
            gender = login_user.gender
            phoneno = login_user.phone
            bundle = dict()
            #name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            if gender==1:
                gender = str("Male")
            elif gender==2:
                gender = str("Female")
            elif gender==3:
                gender = str("Transgender")
            bundle = {'first_name': fname, 'last_name': lname, 'gender': gender, 'phone': phoneno}
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
        userdetail = dict()
        userdetail = {'first_name': first_name, 'last_name': last_name, 'gender': gender_string, 'phone': phone}
    
        return render(request, self.template_name, {'current_user':userdetail})
#______________________________________________User details for dynamic url____________________________________
class CasualUserDetailView(View):
    template_name = 'casual_user/casualuserdetails.html'

    def get(self, request, casualuser):
        username = casualuser

        user = User.objects.get(username = username)
        try:
            casual_user = PremiumUser.objects.get(user = user)
        except:
            pass
        try:
            casual_user = CasualUser.objects.get(user = user)
        except:
            pass
        fname = str(casual_user.user.first_name)
        lname = str(casual_user.user.last_name)
        casualuser = {'first_name': fname, 'last_name':lname, 'date_of_birth':casual_user.date_of_birth, 'gender':casual_user.gender,'email':casual_user.email, 'phone':casual_user.phone }
        return render(request, self.template_name, {'casualuser': casualuser})


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


class ListUserView(View):
    template_name = 'casual_user/list_user.html'
    
    def get(self, request):
        current_user = request.user
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
                                return redirect('casual_user:friendrequest')
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
        return HttpResponseRedirect(reverse('casual_user:listuser'))
        # return render(request, self.template_name, {'bundle': bundle})

class FriendRequestView(View):
    template_name = 'casual_user/listfriendrequest.html'
    def get(self, request):
        current_user = request.user
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
        friendrequestObj = FriendRequest.objects.get(requestto = current_user.username)
        friendlist = friendrequestObj.requestfrom
        friendBundle = {}
        for username in friendlist:
            userObj = User.objects.get(username = username)
            name = str(userObj.first_name) + ' ' +  str(userObj.last_name)
            friendBundle[username] = name
        return render(request, self.template_name, {'friendBundle': friendBundle})

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
        current_user_friendlist = []

    current_user = []
    if current_user_friendlist:
        current_user = zip(current_user_friendlist, name_of_friendlist)
    else:
        current_user = []

    return current_user, have_friend

#for display friendlist
class FriendView(View):
    template_name = 'casual_user/friend.html'

    def get(self, request):
        current_user = request.user
        username1 = current_user.username

        current_user, have_friend = showfrndlist(username1)
        return render(request, self.template_name, {'current_user': current_user})

    def post(self, request):
        current_user = request.user
        username1 = current_user.username
        current_user_friendlist, have_friend = showfrndlist(username1)

        for i,j in current_user_friendlist:
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

        current_user, have_friend = showfrndlist(username1)
        return render(request, self.template_name, {'current_user': current_user})

#_________________________________________________Wallet_____________________________________________________

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

            wallet = Wallet.objects.get(username=username)

            if wallet.transactions_left == 0:
                form.add_error('amount', "You don't have any transactions remaining for the month.")
            else: 
                wallet.amount += float(amount)
                wallet.transactions_left -= 1
                wallet.save()

                # Add to Transactions table
                Transaction(sender=username, receiver=username, amount=amount, timestamp=datetime.now(tz=None)).save()

                w_dict = dict() 

                w_dict['Account Type'] = wallet.user_type
                w_dict['Amount'] = wallet.amount
                w_dict['Remaining Transactions'] = wallet.transactions_left

                return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})

        return render(request, self.template_name, {'form': form})

class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'casual_user/sendmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        # friend_list = None
        # try:
        #     friend_list = Friend.objects.get(username=request.user).friend_list
        # except:
        #     friend_list = []
        # if len(friend_list) > 0:
        #     return render(request, self.template_name, {'form': form})
        # else:
        #     return render(request, )
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            send_to = form.cleaned_data['send_to']

            # Implement OTP functionality here

            sender_wallet = Wallet.objects.get(username=current_user)
            receiver_wallet = Wallet.objects.get(username=send_to)

            if sender_wallet.transactions_left == 0:
                form.add_error('amount', "You don't have any transactions remaining for the month.")
            else:
                # Check for available balance
                if float(amount) <= sender_wallet.amount:
                    sender_wallet.amount -= float(amount)
                    sender_wallet.transactions_left -= 1    # Assumption: Sending money causes one transaction of the sender to be exhausted.
                    receiver_wallet.amount += float(amount)
                    sender_wallet.save()
                    receiver_wallet.save()

                    # Add to Transactions table
                    Transaction(sender=current_user, receiver=send_to, amount=amount, timestamp=datetime.now(tz=None)).save()

                    w_dict = dict() 

                    w_dict['Account Type'] = sender_wallet.user_type
                    w_dict['Amount'] = sender_wallet.amount
                    w_dict['Remaining Transactions'] = sender_wallet.transactions_left

                    return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})
                else:
                    form.add_error('amount', "You don't have enough balance.")

        return render(request, self.template_name, {'form': form})

class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'casual_user/requestmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            request_from = form.cleaned_data['request_from']

            # Implement OTP functionality here

            sender = Wallet.objects.get(username=current_user)

            if sender.transactions_left == 0:
                form.add_error('amount', "You don't have any transactions remaining for the month.")
            else:
                # check number of pending requests made
                pending_requests = len(Request.objects.filter(sender=current_user, status=0))
                
                if sender.transactions_left - pending_requests > 0:
                    # Add entry to Request table
                    req_count = len(Request.objects.all())
                    req_id = "RQST-" + str(req_count + 1)
                    Request(request_id=req_id, sender=current_user, receiver=request_from, amount=float(amount), status=0).save()

                    # Assumption: If the request is accepted, then no. of transactions is deducted by one.

                    w_dict = dict()

                    w_dict['Account Type'] = sender.user_type
                    w_dict['Amount'] = sender.amount
                    w_dict['Remaining Transactions'] = sender.transactions_left

                    return render(request, 'casual_user/mywallet.html', {'wallet': w_dict})
                else:
                    form.add_error('amount', "You have transactions pending. Can't request at this point.")

        return render(request, self.template_name, {'form': form})

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

        pay_requests = Request.objects.filter(receiver=current_user, status=0)
        bundle = dict()
        bundle['requests'] = pay_requests
        return render(request, self.template_name, {'pay_req': bundle})

#_________________________________________________Group________________________________________________________

#function needed in group search 
def request_group(current_user, search_name):
    group_name_list = AddGroup.objects.filter(name__icontains = search_name)
    group_name_list = group_name_list.exclude(admin = current_user.username)

    group_status=[]
    

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

class ListGroupView(View):
    template_name = 'casual_user/list_group.html'
    
    def get(self, request):
        current_user = request.user
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
                            return HttpResponseRedirect(reverse('casual_user:listgroup'))
                        except:
                            group = GroupRequest()
                            group.admin = admin ; group.name = name
                            group.status = 2
                            group.members = [] 
                            group.members.append(username); group.save()
                            #bundle update
                            statusl = 2
                            # return render(request, self.template_name, {'bundle': bundle})
                            return HttpResponseRedirect(reverse('casual_user:listgroup'))
                        
                    else:
                        #message.info NOT WORKING (but not a problem, code working fine)
                        messages.info(request, 'Please recharge.')
                        # return render(request, self.template_name, {'bundle': bundle})
                        return HttpResponseRedirect(reverse('casual_user:listgroup'))

                elif request.POST.dict()[str(keyl)] == "leave":
                    admin = groupadminusernamel; name = groupnamel
                    group = AddGroup.objects.get(admin = admin, name = name)
                    group.members.remove(username)
                    group.save()
                    statusl = 1
                    # return render(request, self.template_name, {'bundle': bundle})
                    return HttpResponseRedirect(reverse('casual_user:listgroup'))
            except:
                pass
        return HttpResponseRedirect(reverse('casual_user:listgroup'))
        # return render(request, self.template_name, {'bundle': bundle})

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

class JoinedGroupView(View):
    template_name = 'casual_user/yourjoinedgroup.html'
    
    def get(self, request):
        current_user = request.user
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
        return HttpResponseRedirect(reverse('casual_user:yourjoinedgroup'))

#_________________________________________________Message______________________________________________________
def getfriendlist(username1):
    try:
        have_friend = Friend.objects.get(username = username1)
        friendlist = []
        for i in have_friend.friend_list:
            userObj = User.objects.get(username= i)
            if userObj.user_type is not 1:
                friendlist.append(i)

    except:
        friendlist = []
    return friendlist

class Saveuser:
    username = ""
usernameObj = Saveuser() 


class InboxView(View):
    template_name = 'casual_user/inbox.html'

    def get(self, request):
        current_user = request.user
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

                if request.POST.dict()[selected_user] == "View Message":
                    usernameObj.username = ""
                    usernameObj.username = selected_user
            except:
                pass
        return redirect('casual_user:chat')

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

class ChatView(View):
    template_name = 'casual_user/chat.html'
    def get(self, request):
        current_user = request.user
        username1 = current_user.username; sender = username1
        receiver = usernameObj.username
        
        updatemessages = showmessages(sender, receiver)

        msg = {'updatemessages':updatemessages}
        return render(request, self.template_name, {'msg': msg})


class LogoutView(View):
    template_name = 'login/login.html'

    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))
