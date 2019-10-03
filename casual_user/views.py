from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from .models import CasualUser, Post, Friend, Wallet, Request, Transaction
from login.models import User

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from .forms import AddMoneyForm, SendMoneyForm, RequestMoneyForm

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

def showfrndlist(username1):
    try:
        have_friend = Friend.objects.get(username=username1)
        current_user_friendlist = list(have_friend.friend_list)
    except:
        current_user_friendlist = []

    return have_friend, current_user_friendlist

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

            have_friend, current_user_friendlist = showfrndlist(username1)

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

            have_friend, current_user_friendlist = showfrndlist(username1)
                
            current_user = dict()
            current_user[username1] = current_user_friendlist

            return render(request, self.template_name, {'current_user': current_user})

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


