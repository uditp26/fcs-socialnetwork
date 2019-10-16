from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from casual_user.models import Wallet, Transaction, Request, Post, Friend
from login.models import User
from .models import PremiumUser, AddGroup, Group, GroupRequest, GroupPlan
from .forms import AddGroupForm, GroupPlanForm, AddMoneyForm, SendMoneyForm, RequestMoneyForm, EditProfileForm

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from datetime import datetime
from datetime import date

import sys

def priceofplan(plantype):
    if plantype == 1:
        price = 50
        noofgroup = 2
    elif plantype == 2:
        price = 100
        noofgroup = 4
    else:
        price = 150
        noofgroup = sys.float_info.max
    return price, noofgroup

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
    template_name = 'premium_user/homepage.html'

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

#pass to groupdetails.html
def getgroupdetails(current_user):
    groups = AddGroup.objects.filter(admin = current_user.username)
    groupplan = GroupPlan.objects.get(customer = current_user.username)
    bundle = {}
    groupinfo = {}
    key = 1; anotherkey  = 11
    for group in groups:
        m = ""; members = group.members
        for i in members:
            m = m + " " + "'"+i+"'"
        temp1 = {}; temp1[group.price] = m
        temp2 = {}; temp2[group.name] = temp1
        groupinfo[key] = temp2
        key+=1
    groupplaninfo = {}
    current_date = datetime.now().date()
    rechargedate = groupplan.recharge_on.date()
    days = 30 - int((current_date - rechargedate).days)
    noofgroups = groupplan.noofgroup
    groupplaninfo[days] = noofgroups
    bundle[anotherkey] = groupinfo; anotherkey += 1
    bundle[anotherkey] = groupplaninfo
    
    return bundle
         
class GroupDetailsView(View):
    template_name = 'premium_user/groupdetails.html'

    def get(self, request):
        current_user = request.user
        
        bundle = getgroupdetails(current_user)
        return render(request, self.template_name, {'bundle':bundle})

class ProfileView(View):
    template_name = 'premium_user/myprofile.html'

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
    template_name = 'premium_user/editprofile.html'
    
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


class GroupPlanFormView(View):
    form_class = GroupPlanForm
    template_name = 'premium_user/groupplan_form.html'
    
    def get(self, request):
        form = self.form_class(None)
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
                    print("current_date : ", current_date)
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


class AddGroupFormView(View):
    form_class = AddGroupForm
    template_name = 'premium_user/addgroup_form.html'
    
    def get(self, request):
        current_user = request.user
        username = current_user.username
        try:
            groupplanofuser = GroupPlan.objects.get(customer = username)
            noofgroup = groupplanofuser.noofgroup
            # Recharge validity check
            current_date = datetime.now().date()
            rechargedate = groupplanofuser.recharge_on.now().date()
            days = int((rechargedate - current_date).days)
            if noofgroup > 0 and days <= 30:
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


#______________________________________________________ wallet_____________________________________________

class WalletView(View):
    template_name = 'premium_user/mywallet.html'
    print("Enter premium_user wallet")
    def get(self, request):
        current_user = request.user
        wallet = Wallet.objects.get(username = current_user.username)

        w_dict = dict() 

        w_dict['Account Type'] = wallet.user_type
        w_dict['Amount'] = wallet.amount
        w_dict['Remaining Transactions'] = wallet.transactions_left
        
        return render(request, self.template_name, {'wallet': w_dict})

class AddMoneyFormView(View):
    form_class = AddMoneyForm
    template_name = 'premium_user/addmoney.html'

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

                return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})

        return render(request, self.template_name, {'form': form})

class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'premium_user/sendmoney.html'

    def get(self, request):
        form = self.form_class(request.user)
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

                    return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})
                else:
                    form.add_error('amount', "You don't have enough balance.")

        return render(request, self.template_name, {'form': form})

class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'premium_user/requestmoney.html'

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

                    return render(request, 'premium_user/mywallet.html', {'wallet': w_dict})
                else:
                    form.add_error('amount', "You have transactions pending. Can't request at this point.")

        return render(request, self.template_name, {'form': form})

class PendingRequestsView(View):
    template_name = 'premium_user/pendingrequests.html'

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


#__________________________________________________________________________________________________________
class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))
