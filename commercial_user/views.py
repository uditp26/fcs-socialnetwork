import itertools
from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from login.models import User
from .models import CommercialUser, Pages
from casual_user.models import Wallet, Transaction, Request, Post, Friend, FriendRequest, CasualUser, Timeline
from premium_user.models import PremiumUser, AddGroup, Group, GroupRequest, GroupPlan, Message
from .forms import AddGroupForm, EditProfileForm, AddMoneyForm, SendMoneyForm, RequestMoneyForm, CreatePagesForm, AddMoneyNewForm, OTPVerificationForm, VerifyPanForm, GroupPlanForm

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

decorators = [cache_control(no_cache=True, must_revalidate=True, no_store=True), login_required(login_url='http://127.0.0.1:8000/login/')]

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

def updateExistingUser(curr_user, first_name, last_name, gender, phone):
    curr_user.first_name = first_name
    curr_user.last_name = last_name
    curr_user.save()

    if curr_user.user_type == 1:
        curr_user = CasualUser.objects.get(user=curr_user)
    elif curr_user.user_type == 2:
        curr_user = PremiumUser.objects.get(user=curr_user)
    else:
        curr_user = CommercialUser.objects.get(user=curr_user)
    curr_user.gender = gender
    curr_user.phone = phone
    curr_user.save()

def GetAllPageInfo(current_user):
    allpageobjects = Pages.objects.all()
    alltitles = []
    alllinks = []
    alldescriptions = []
    authors = []
    
    for obj in allpageobjects:
        titlelist = obj.title
        descriptionlist = obj.description
        linklist = obj.page_link
        username = obj.username
        
        for description in descriptionlist:
            alldescriptions.append(description)
        for title in titlelist:
            alltitles.append(title)
        for link in linklist:
            alllinks.append(link)
        k=0
        while k < len(linklist):
            authors.append(username)
            k += 1
    commercial_user = CommercialUser.objects.get(user=current_user)
    userfullname = commercial_user.user.first_name+" "+commercial_user.user.last_name
    details = dict()
    details = {'user':userfullname, 'authors':authors, 'alltitles':alltitles, 'alldescriptions':alldescriptions, 'alllinks':alllinks}
    
    return details    

@method_decorator(decorators, name='dispatch')
class PaymentView(View):

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            #bundle = genBundle(current_user)
            wallet = Wallet.objects.get(username=current_user.username)
            commercial_user = CommercialUser.objects.get(user=current_user)
            subs_paid = commercial_user.subscription_paid
            statusofrequest = commercial_user.statusofrequest
            #print(subs_paid)
            amount = wallet.amount
            if statusofrequest == 2:
                if subs_paid == True:
                    return redirect('commercial_user:homepage')
                else:
                    return redirect('commercial_user:addmoneytosubscribe')
            elif statusofrequest == 1 or statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')
            else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied')

def notifyAdmin(current_user):
    c_user = User.objects.get(username=str(current_user))
    message = c_user.username + ' has requested verification for commercial user account. \n\nEmail of the user: ' + c_user.email + ' .'

    c = send_mail(
        'Verification for Commercial User',
        message,
        'admin@fcs.com',
        ['admin@fcs.com'],
        fail_silently=False,
    )

    return c

@method_decorator(decorators, name='dispatch')
class VerifyPanFormView(View):
    form_class = VerifyPanForm
    template_name = 'commercial_user/verifypan.html'

    def get(self, request):
        form = self.form_class(None)
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            c_user = CommercialUser.objects.get(user=current_user)
            statusofrequest = c_user.statusofrequest
            
            commercial_user = dict()
        
            if statusofrequest == 2: #verified, redirect immediately to payment and subscribe page in POST
                return redirect('commercial_user:addmoneytosubscribe')
            elif statusofrequest == 4 or statusofrequest == 1: #pending
                commercial_user = {'status':statusofrequest, 'form':form}
                return render(request, self.template_name, {'commercial_user': commercial_user})
            else: #not allowed, declined, not verified
                return redirect('commercial_user:denied')
        
    def post(self, request):
        current_user = request.user
        
        if request.POST.dict()["buttonid2"] == "Verify-Account":
            wallet = Wallet.objects.get(username=current_user.username)
            c_user = CommercialUser.objects.get(user=current_user)
            requeststatus = c_user.statusofrequest
            if requeststatus == 1:
                c_user.statusofrequest = 4
                c_user.save()
                
                # Send email to admin
                c = notifyAdmin(current_user)

                if c == 1:
                    return HttpResponseRedirect(reverse('commercial_user:verifypan'))
                else:
                    # error - Mail not sent to admin
                    pass
            elif requeststatus == 4:
                return HttpResponseRedirect(reverse('commercial_user:verifypan'))
                
            elif requeststatus == 2:
                return redirect('commercial_user:addmoneytosubscribe')
            elif requeststatus == 3:
                return redirect('commercial_user:denied')
       

@method_decorator(decorators, name='dispatch')
class DeniedAccessView(View):
    template_name = 'commercial_user/verifypan.html'

    def get(self, request):
        
        #return render(request, self.template_name, {'form': form})
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            c_user = CommercialUser.objects.get(user=current_user)
            subs_paid = c_user.subscription_paid
            statusofrequest = c_user.statusofrequest
            if statusofrequest == 3:
                commercial_user = dict()
                commercial_user = {'status':statusofrequest}
                return render(request, self.template_name, {'commercial_user': commercial_user})
            elif statusofrequest == 2:
                if subs_paid == False:
                    return redirect('commercial_user:addmoneytosubscribe')
                else:
                    return redirect('commercial_user:homepage')
            else:
                return redirect('commercial_user:verifypan')
                

@method_decorator(decorators, name='dispatch')
class AddMoneyFormToSubscribeView(View):
    form_class = AddMoneyNewForm
    template_name = 'commercial_user/addmoneynew.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            #bundle = genBundle(current_user)
            wallet = Wallet.objects.get(username=current_user.username)
            c_user = CommercialUser.objects.get(user=current_user)
            subs_paid = c_user.subscription_paid
            statusofrequest = c_user.statusofrequest
            #print(subs_paid)
            amount = wallet.amount
           
            commercial_user = dict()
        
            form_class = AddMoneyNewForm
            form = self.form_class(None)
            if statusofrequest == 2:
                if subs_paid == True:
                    return redirect('commercial_user:homepage')
                elif subs_paid == False and amount<5000:
                    commercial_user = {'amount':amount, 'status':subs_paid, 'form':form}
                elif subs_paid == False and amount>=5000:
                    commercial_user = {'amount':amount, 'status':subs_paid}
                return render(request, self.template_name, {'commercial_user': commercial_user})
            elif statusofrequest == 1 or statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')
            else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied')
            
    def post(self, request):
        #form = self.form_class(request.POST)
        current_user = request.user
        #form_class = AddMoneyForm
        form = self.form_class(request.POST)
        c_user = CommercialUser.objects.get(user=current_user)
        statusofrequest = c_user.statusofrequest

        if statusofrequest == 2:
            #if request.POST.dict().get("buttonid") is None:
            if request.POST.dict()["buttonid"] == "Add-Money":
                wallet = Wallet.objects.get(username=current_user.username)
        
                if form.is_valid():
                    amount = form.cleaned_data['amount']
                if amount is None:
                    form.add_error('amount', "Please enter the amount. Field is empty.")
                    # status = c_user.subscription_paid
                    # commercial_user = {'amount':wallet.amount, 'status':status, 'form':form}
                    # return render(request, self.template_name, {'commercial_user':commercial_user})
                elif float(amount)>0:
                    wallet.amount += float(amount)
                    wallet.transactions_left -= 1
                    wallet.save()
                    
                    Transaction(sender=current_user, receiver="Admin", amount=amount, timestamp=timezone.now()).save()
                    status = c_user.subscription_paid
                    form = self.form_class(None)
                    commercial_user = dict()
                    
                    if wallet.amount>=5000:
                    #    redirect('commercial_user:addmoneytosubscribe')
                        #commercial_user = {'amount':wallet.amount, 'status':status}
                        return HttpResponseRedirect(reverse('commercial_user:addmoneytosubscribe'))
                        #return render(request, self.template_name, {'commercial_user':commercial_user})
                    else:
                        #commercial_user = {'amount':wallet.amount, 'status':status, 'form':form}
                        #return render(request, self.template_name, {'commercial_user':commercial_user})
                        return HttpResponseRedirect(reverse('commercial_user:addmoneytosubscribe'))
                else:
                    
                    form.add_error('amount', "You have entered value less than Rs 1.")
                    commercial_user = dict()
                    
                    status = c_user.subscription_paid
                    commercial_user = {'amount':wallet.amount, 'status':status,'form':form}
                    
                    return render(request, self.template_name, {'commercial_user':commercial_user})
            
            elif request.POST.dict()["buttonid"] == "Subscribe":
                c_user = CommercialUser.objects.get(user=current_user)
                wallet = Wallet.objects.get(username=current_user.username)
                    

                if c_user.subscription_paid == False and wallet.amount >= 5000.0:
                    c_user.subscription_paid = True
                    c_user.save()
                    wallet.amount -= 5000.0
                    wallet.save()
                    status = c_user.subscription_paid
                    if status == True:
                        username = c_user.user.username
                        url = reverse('commercial_user:homepage')
                        return HttpResponseRedirect(url)
                        
                    else:
                        commercial_user = dict()
                        form = self.form_class(None)
                        commercial_user = {'amount':wallet.amount, 'status':status, 'form':form}
                        return render(request, self.template_name, {'commercial_user':commercial_user})    
                    
                elif c_user.subscription_paid == True:
                    return redirect('commercial_user:homepage')
                    
                else:
                    form.add_error('amount', "You do not have enough balance(Rs 5000) to pay subscription charges.")
                    commercial_user = dict()
                    #form = self.form_class(None)
                    status = c_user.subscription_paid
                    commercial_user = {'amount':wallet.amount, 'status':status,'form':form}
                    
                    return render(request, self.template_name, {'commercial_user':commercial_user})

        elif statusofrequest == 1 or statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')
                      
                
        
@method_decorator(decorators, name='dispatch')
class MainHomepageView(View):
    template_name = 'commercial_user/mainhomepage.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            c_user = CommercialUser.objects.get(user=current_user)
            if c_user.statusofrequest == 2:
                if c_user.subscription_paid == True:
                    bundle = genBundle(current_user)
                    return render(request, self.template_name, {'bundle':bundle})
                else:
                    return redirect('commercial_user:addmoneytosubscribe')
            elif c_user.statusofrequest == 1 or c_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied')


    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                savePost(self, request, current_user)
                bundle = genBundle(current_user)
                return render(request, self.template_name, {'bundle':bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 1 or c_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied')

def getgroupdetails(current_user):
    bundle = {}
    try:
        groups = AddGroup.objects.filter(admin = current_user.username)
        groupplan = GroupPlan.objects.get(customer = current_user.username)
        print("YES")
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
    template_name = 'commercial_user/groupdetails.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle = getgroupdetails(current_user)
                return render(request, self.template_name, {'bundle':bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page 
                return redirect('commercial_user:denied')

        else: #pending, not validated yet
                return redirect('commercial_user:verifypan')
        

@method_decorator(decorators, name='dispatch')
class ProfileView(View):
    template_name = 'commercial_user/myprofile.html'

    def get(self, request):
        current_user = request.user

        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CommercialUser.objects.get(user=current_user)
            if casual_user.statusofrequest == 2:
                if casual_user.subscription_paid == True:
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
                else:
                    return redirect('commercial_user:addmoneytosubscribe')

            elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied')   

def createrandomurl(title, username):
    if len(title) > 20:
        newtitle = title[:20]
        newtitle = newtitle.replace(" ","-")
    else:
        newtitle = title
        newtitle = newtitle.replace(" ","-")
    lastchar = newtitle[-1:]
    if lastchar == '-':
        lenoftitle = len(newtitle)
        newtitle = newtitle[:lenoftitle-1]
    prefix = username+"-"
    newtitle = prefix+newtitle
    
    # check for unique url
    page_links = Pages.objects.get(username=username).page_link
    
    #similar_url = len(Pages.objects.filter(title=newtitle))

    ntitle = newtitle
    i = 1
    for p in page_links:
        if ntitle == p:
            ntitle = newtitle + "-" + str(i)
            i += 1
    
    return ntitle

@method_decorator(decorators, name='dispatch')
class CreatePagesFormView(View):
    form_class = CreatePagesForm
    template_name = 'commercial_user/createpages.html'

    def get(self, request):
        current_user = request.user
        commercial_user = CommercialUser.objects.get(user=current_user)
        form = self.form_class(None)
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            if commercial_user.statusofrequest == 2:
                if commercial_user.subscription_paid == True:
                    return render(request, self.template_name, {'form': form})
                else:
                    return redirect('commercial_user:addmoneytosubscribe')
            
            elif commercial_user.statusofrequest == 1 or commercial_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied') 

    def post(self, request):
        current_user = request.user
        commercial_user = CommercialUser.objects.get(user=current_user)
        print(commercial_user.statusofrequest)
        if commercial_user.statusofrequest == 2:
            if commercial_user.subscription_paid == True:
                username = commercial_user.user.username

                form = self.form_class(request.POST)

                if form.is_valid():
                    title = form.cleaned_data['page_title']
                    description = form.cleaned_data['page_description']
                
                    #page_link 
                

                #form_class = CreatePagesDetailForm
                #form = self.form_class(None)
                url_generated = createrandomurl(title, username)
                page_link = url_generated
                pagesobject = Pages.objects.get(username=username)
                pagesobject.title.append(title)
                pagesobject.description.append(description)
                pagesobject.page_link.append(page_link)
                pagesobject.save()
                
                # Create a public post for current user
                # Here's a new page I've created:
                # Page Title: <title>
                # Author: <author>
                # <link to page> <a href="{% url 'commercial_user:viewpage' bundle.username link %}"><title></a>
                
                return HttpResponseRedirect(reverse('commercial_user:createpage'))
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif commercial_user.statusofrequest == 1 or commercial_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

@method_decorator(decorators, name='dispatch')
class MyPagesListView(View):
    template_name = 'commercial_user/mypages.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            commercial_user = CommercialUser.objects.get(user=current_user)

            if commercial_user.statusofrequest == 2:
                if commercial_user.subscription_paid == True:
                    mypagedetail = dict()
                    username = commercial_user.user.username
                    author = commercial_user.user.first_name+" "+commercial_user.user.last_name
                    page_object = Pages.objects.get(username=username)

                    titles = list(page_object.title)
                    links = list(page_object.page_link)

                    link_dict = dict()

                    for i, l in enumerate(links):
                        link_dict[l] = titles[i]
                    
                    mypagedetail = {'author':author, 'username':username, 'link_dict':link_dict}
                    
                    return render(request, self.template_name, {'bundle': mypagedetail})
                else:
                    return redirect('commercial_user:addmoneytosubscribe')

            elif commercial_user.statusofrequest == 1 or commercial_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied') 

@method_decorator(decorators, name='dispatch')
class ViewMyPageView(View):
    template_name = 'commercial_user/viewpage.html'

    def get(self, request, username, url):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            commercial_user = CommercialUser.objects.get(user=current_user)

            if commercial_user.statusofrequest == 2:
                if commercial_user.subscription_paid == True:
                    p_obj = Pages.objects.get(username=username)

                    bundle = dict()
                    title = ""
                    author = ""
                    body = ""

                    for i in range(len(p_obj.page_link)):
                        if p_obj.page_link[i] == url:
                            title = p_obj.title[i]
                            usr = User.objects.get(username=username)
                            author = usr.first_name + " " + usr.last_name
                            body = p_obj.description[i]
                            break
                    
                    bundle['title'] = title
                    bundle['author'] = author
                    bundle['body'] = body

                    return render(request, self.template_name, {'bundle':bundle})
                else:
                    return redirect('commercial_user:addmoneytosubscribe')

            elif commercial_user.statusofrequest == 1 or commercial_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied') 


@method_decorator(decorators, name='dispatch')
class EditProfileFormView(View):
    form_class = EditProfileForm
    template_name = 'commercial_user/editprofile.html'
    
    def get(self, request):
        current_user = request.user
        print(type(current_user))
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CommercialUser.objects.get(user=current_user)
            if casual_user.statusofrequest == 2:
                if casual_user.subscription_paid == True:    
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
                else:
                    return redirect('commercial_user:addmoneytosubscribe')

            elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

            else: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page
                return redirect('commercial_user:denied') 


    def post(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:  
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
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

@method_decorator(decorators, name='dispatch')
class UserProfileView(View):
    template_name = 'commercial_user/userprofile.html'

    def get(self, request, username):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page 
                return redirect('commercial_user:denied')

        else: #pending, not validated yet
                return redirect('commercial_user:verifypan')

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
    template_name = 'commercial_user/list_user.html'
    
    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle, user_name_list = user_friendlist(current_user, request)
                return render(request, self.template_name, {'bundle': bundle})

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle, user_name_list = user_friendlist(current_user, request)

                for i in user_name_list:
                    try:
                        selected_user = i.username
                        if request.POST.dict()[selected_user] == "Add Friend":
                            try:
                                try:
                                    requestto1 = FriendRequest.objects.get(requestto = current_user.username)
                                    if selected_user in requestto1.requestfrom:
                                        return redirect('commercial_user:friendrequest')
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
                return HttpResponseRedirect(reverse('commercial_user:listuser'))        

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

@method_decorator(decorators, name='dispatch')
class FriendRequestView(View):
    template_name = 'commercial_user/listfriendrequest.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

       

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
        
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
                return HttpResponseRedirect(reverse('commercial_user:friendrequest'))
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

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

@method_decorator(decorators, name='dispatch')
class FriendView(View):
    template_name = 'commercial_user/friend.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                friends_zip, have_friend = showfrndlist(current_user)
                friends_zip = checkPrivacySettings(friends_zip)
                return render(request, self.template_name, {'current_user': friends_zip})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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
                            return redirect('commercial_user:postcontent')
                    except:
                        pass

                return HttpResponseRedirect(reverse('commercial_user:friend'))
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

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
    template_name = 'commercial_user/list_group.html'
    
    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                search_name = findGroup(request).lower()
                bundle = request_group(current_user, search_name)
                if bundle:
                    return render(request, self.template_name, {'bundle': bundle})
                else:
                    bundle = {}
                    return render(request, self.template_name, {'bundle': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:

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
                                    return HttpResponseRedirect(reverse('commercial_user:listgroup'))
                                except:
                                    group = GroupRequest()
                                    group.admin = admin ; group.name = name
                                    group.status = 2
                                    group.members = [] 
                                    group.members.append(username); group.save()
                                    #bundle update
                                    statusl = 2
                                    return HttpResponseRedirect(reverse('commercial_user:listgroup'))
                                
                            else:
                                #message.info NOT WORKING (but not a problem, code working fine)
                                messages.info(request, 'Please recharge.')
                                # return render(request, self.template_name, {'bundle': bundle})
                                return HttpResponseRedirect(reverse('commercial_user:listgroup'))

                        elif request.POST.dict()[str(keyl)] == "leave":
                            admin = groupadminusernamel; name = groupnamel
                            group = AddGroup.objects.get(admin = admin, name = name)
                            group.members.remove(username)
                            group.save()
                            statusl = 1
                            return HttpResponseRedirect(reverse('commercial_user:listgroup'))
                    except:
                        pass
                return HttpResponseRedirect(reverse('commercial_user:listgroup'))
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

@method_decorator(decorators, name='dispatch')
class GroupPlanFormView(View):
    form_class = GroupPlanForm
    template_name = 'commercial_user/groupplan_form.html'
    
    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                form = self.form_class(None)
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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
                            return render(request, 'commercial_user/plansuccessfullyopted.html', {'name': name})

                        else:
                            form.add_error('plantype', "You don't have sufficient balance.")

                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

@method_decorator(decorators, name='dispatch')
class AddGroupFormView(View):
    form_class = AddGroupForm
    template_name ='commercial_user/addgroup_form.html'
    
    #display blank form
    def get(self, request):
        form = self.form_class(None)
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
                return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

    #put data inside blank text fields 
    def post(self, request):
        current_user = request.user
        form = self.form_class(request.POST)
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

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

@method_decorator(decorators, name='dispatch')
class ListRequestView(View):
    template_name = 'commercial_user/listrequest.html'
    
    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                bundle, group_request = return_bundle_for_request(current_user)

                return render(request, self.template_name, {'bundle': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 


    def post(self, request):
        current_user = request.user
        bundle, group_request = return_bundle_for_request(current_user)
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

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
    template_name = 'commercial_user/deletegroup.html'
    
    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle = listowngroup(current_user)
                return render(request, self.template_name, {'bundle': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle = listowngroup(current_user)

                for group in bundle:
                    try:
                        if request.POST.dict()[str(group)] == "Delete":
                            groupobj = Group.objects.get(admin = current_user.username)
                            groupobj.group_list.remove(group); groupobj.save()
                            addgroupObj = AddGroup.objects.get(admin = current_user.username, name = group)
                            addgroupObj.delete()
                            break
                    except:
                        pass

                bundle = listowngroup(current_user)
                return render(request, self.template_name, {'bundle': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')

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
    template_name = 'commercial_user/yourjoinedgroup.html'
    
    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle = listjoinedgroup(current_user)
                return render(request, self.template_name, {'bundle': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                bundle = listjoinedgroup(current_user)
                for key, adusername, adname, groupname, price, gmembers in bundle:
                    try:
                        if request.POST.dict()[str(key)] == "leave":
                            group = AddGroup.objects.get(admin = adusername, name = groupname)
                            group.members.remove(current_user.username)
                            group.save()
                    except:
                        pass
                return HttpResponseRedirect(reverse('commercial_user:yourjoinedgroup'))
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

@method_decorator(decorators, name='dispatch')
class WalletView(View):
    template_name = 'commercial_user/mywallet.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                wallet = Wallet.objects.get(username=current_user.username)

                w_dict = dict() 

                w_dict['Account Type'] = wallet.user_type
                w_dict['Amount'] = wallet.amount
                w_dict['Remaining Transactions'] = "No Limit"       # backend has 10000 transactions set

                return render(request, self.template_name, {'wallet': w_dict})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

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
    template_name = 'commercial_user/addmoney.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                form = self.form_class(None)
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

    def post(self, request):
        form = self.form_class(request.POST)
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        print(casual_user.subscription_paid)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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
                            return HttpResponseRedirect(reverse('commercial_user:otpverify'))
                    else:
                        form.add_error('amount', 'OTP generation failed. Please check your network connection.')

                return render(request, self.template_name, {'form': form})

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

@method_decorator(decorators, name='dispatch')
class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'commercial_user/sendmoney.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                form = self.form_class(request.user)
                friend_list = None
                try:
                    friend_list = Friend.objects.get(username=request.user).friend_list
                except:
                    friend_list = []
                if len(friend_list) > 0:
                    return render(request, self.template_name, {'form': form})
                else:
                    return redirect('commercial_user:nofriends')
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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
                            return redirect('commercial_user:otpverify')
                        else:          
                            form.add_error('amount', 'OTP generation failed. Please check your network connection.')

                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

@method_decorator(decorators, name='dispatch')
class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'commercial_user/requestmoney.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                form = self.form_class(request.user)
                friend_list = None
                try:
                    friend_list = Friend.objects.get(username=request.user).friend_list
                except:
                    friend_list = []
                if len(friend_list) > 0:
                    return render(request, self.template_name, {'form': form})
                else:
                    return redirect('commercial_user:nofriends')
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

    def post(self, request):
        current_user = request.user
        form = self.form_class(current_user, request.POST)
        casual_user = CommercialUser.objects.get(user=current_user)

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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
                                return redirect('commercial_user:otpverify')
                            else:
                                form.add_error('amount', "You have transactions pending. Can't request at this point.")
                    else:
                        form.add_error('amount', 'OTP generation failed. Please check your network connection.')

                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

@method_decorator(decorators, name='dispatch')
class PendingRequestsView(View):
    template_name = 'commercial_user/pendingrequests.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                pay_requests = Request.objects.filter(receiver=current_user, status=0)
                bundle = dict()
                bundle['requests'] = pay_requests
                return render(request, self.template_name, {'pay_req': bundle})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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

                return HttpResponseRedirect(reverse('commercial_user:pendingrequests'))

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        
@method_decorator(decorators, name='dispatch')
class OTPVerificationFormsView(View):
    form_class = OTPVerificationForm
    template_name = 'commercial_user/otpverify.html'

    def get(self, request):
        current_user = request.user
        commercial_user = CommercialUser.objects.get(user=current_user)
        if commercial_user.statusofrequest == 2:
            if commercial_user.subscription_paid == True:
                form = self.form_class(None)
                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')
        elif commercial_user.statusofrequest == 3:
            return redirect('commercial_user:denied')
        else:
            return redirect('commercial_user:verifypan')


    def post(self, request):
        current_user = request.user

        form = self.form_class(request.POST)
        current_user = request.user
        commercial_user = CommercialUser.objects.get(user=current_user)
        if commercial_user.statusofrequest == 2:
            if commercial_user.subscription_paid == True:
            
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
                            Transaction(sender=username, receiver=username, amount=float(request.session['amount']), timestamp=timezone.now()).save()

                            request.session.pop('amount', None)
                            request.session.modified = True

                            w_dict = dict() 

                            w_dict['Account Type'] = wallet.user_type
                            w_dict['Amount'] = wallet.amount
                            w_dict['Remaining Transactions'] = wallet.transactions_left

                            return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})

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

                            return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})

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

                            return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})

                        else:
                            form.add_error('otp', 'Unknown transaction!')
                        

                return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')
        elif commercial_user.statusofrequest == 3:
            return redirect('commercial_user:denied')
        else:
            return redirect('commercial_user:verifypan')

def getfriendlist(username1):
    try:
        have_friend = Friend.objects.get(username = username1)
        friendlist  = list(have_friend.friend_list)
    except:
        friendlist = []
    return friendlist

class Saveuser:
    username = ""
usernameObj = Saveuser()

@method_decorator(decorators, name='dispatch')
class InboxView(View):
    template_name = 'commercial_user/inbox.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
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
                return redirect('commercial_user:chat')
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

def saveMessage(self, request, sender, receiver):
    search_msg = request.POST.dict()['messagearea']

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
    template_name = 'commercial_user/chat.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                sender = current_user.username
                receiver = usernameObj.username
                updatemessages = showmessages(sender, receiver)
                msg = {'updatemessages':updatemessages}
                return render(request, self.template_name, {'msg': msg})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

    def post(self, request):

        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                sender = current_user.username
                receiver = usernameObj.username
                saveMessage(self, request, sender, receiver)
                return HttpResponseRedirect(reverse('commercial_user:chat'))

            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        
@method_decorator(decorators, name='dispatch')
class PostContentView(View):
    template_name = 'commercial_user/postcontent.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                owner = request.session.get('owner')
                owner = User.objects.get(username=owner).first_name + " " + User.objects.get(username=owner).last_name
                visitor = request.user
                visitor = User.objects.get(username=visitor).first_name + " " + User.objects.get(username=visitor).last_name
                return render(request, self.template_name, {'owner':owner, 'visitor':visitor})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                owner = request.session.get('owner')
                visitor = request.user
                savePost(request, owner, visitor)
                request.session.pop('trans_type', None)
                request.session.modified = True
                return redirect('commercial_user:friend')
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

@method_decorator(decorators, name='dispatch')
class NofriendsView(View):
    template_name = 'commercial_user/nofriends.html'

    def get(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                return render(request, self.template_name)
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        

@method_decorator(decorators, name='dispatch')
class SettingsView(View):
    template_name = 'commercial_user/settings.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            current_user = request.user
            c_user = CommercialUser.objects.get(user=current_user)
            if c_user.statusofrequest == 2:
                if c_user.subscription_paid == True:
                    level = Timeline.objects.get(username=current_user).level
                    if level:
                        level = "Friends"
                    else:
                        level = "Only Me"
                    return render(request, self.template_name, {'level': level})
                else:
                    return redirect('commercial_user:addmoneytosubscribe')

            elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
                #up for premium or casual user, and redirect to register page 
                return redirect('commercial_user:denied')

            else: #pending, not validated yet
                return redirect('commercial_user:verifypan')
            

    def post(self, request):
        current_user = request.user
        c_user = CommercialUser.objects.get(user=current_user)
        if c_user.statusofrequest == 2:
            if c_user.subscription_paid == True:
                scope = request.POST.dict()['level']
                user_timeline = Timeline.objects.get(username=str(current_user))

                if scope == "0":
                    user_timeline.level = 0
                elif scope == "1":
                    user_timeline.level = 1
                
                user_timeline.save()
                return HttpResponseRedirect(reverse('commercial_user:settings'))
        
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif c_user.statusofrequest == 3: #if not valid pan, then redirect to another page. Suggest user to sign
            #up for premium or casual user, and redirect to register page 
            return redirect('commercial_user:denied')

        else: #pending, not validated yet
            return redirect('commercial_user:verifypan')
        
@method_decorator(decorators, name='dispatch')
class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('login:login'))