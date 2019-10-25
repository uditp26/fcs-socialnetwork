import itertools
from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.http import Http404

from login.models import User
from .models import CommercialUser, Pages
#Post, Friend, Wallet, Request, Transaction
from casual_user.models import Post, Friend, Wallet, Request, Transaction
from premium_user.models import AddGroup, Group, GroupRequest
#from casual_user.models import Friend

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django import forms

from datetime import datetime
from .forms import AddGroupForm, EditProfileForm, AddMoneyForm, SendMoneyForm, RequestMoneyForm, CreatePagesForm, AddMoneyNewForm, VerifyPanForm


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
    casual_user = CommercialUser.objects.get(user=current_user)
    bundle = dict()
    name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
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
    curr_user = CasualUser.objects.get(user=curr_user)
    curr_user.gender = gender
    curr_user.phone = phone
    curr_user.save()

def GetAllPageInfo(current_user):
    allpageobjects = Pages.objects.all()
    alltitles = []
    alllinks = []
    alldescriptions = []
    authors = [] #list of usernames, derive first name and last name from it
    #lists will look like
    #authors = ['s','s','t','t','u','u','u','u'] username stored every time for each title,link,description
    #alltitles = ['hello','hello','hello','hello','hello','hello','hello','hello']
    #alllinks = ['s-hello','s-hello-1','t-hello','t-hello-1','u-hello','u-hello-1','u-hello-2','u-hello-3']
    #alldescriptions = ['hello world','hello world','hello world','hello world',....] contents of each page
    
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


class VerifyPanFormView(View):
    form_class = VerifyPanForm
    template_name = 'commercial_user/verifypan.html'

    def get(self, request):
       
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            c_user = CommercialUser.objects.get(user=current_user)
            statusofrequest = c_user.statusofrequest
            
            commercial_user = dict()
        
            form = self.form_class(None)
            if statusofrequest == 2: #verified, redirect immediately to payment and subscribe page in POST
                return redirect('commercial_user:addmoneytosubscribe')
                #commercial_user = {'status':statusofrequest}
                #return render(request, self.template_name, {'commercial_user': commercial_user})
            elif statusofrequest == 4 or statusofrequest == 1: #pending
                commercial_user = {'status':statusofrequest, 'form':form}
                return render(request, self.template_name, {'commercial_user': commercial_user})
            else: #not allowed, declined, not verified
                return redirect('commercial_user:denied')
        
    def post(self, request):
        #form = self.form_class(request.POST)
        current_user = request.user
        #form_class = VerifyPanForm
        #form = self.form_class(request.POST)
        
    #     #if request.POST.dict().get("buttonid") is None:
        if request.POST.dict()["buttonid2"] == "Verify-Account":
            wallet = Wallet.objects.get(username=current_user.username)
            c_user = CommercialUser.objects.get(user=current_user)
            # if form.is_valid():
            #     pan_card = form.cleaned_data['pan_Card_Number']
            #     previous_pan = c_user.pan
            requeststatus = c_user.statusofrequest
            if requeststatus == 1:
                c_user.statusofrequest = 4
                c_user.save()
                
                #Add code to send email to admin
                # username = c_user.username
                # send_email(sender=admin@gmail.com,subject="Verification request",body="Request from Username="+username)
                return HttpResponseRedirect(reverse('commercial_user:verifypan'))
                
            elif requeststatus == 4:
                return HttpResponseRedirect(reverse('commercial_user:verifypan'))
                
            elif requeststatus == 2:
                return redirect('commercial_user:addmoneytosubscribe')
            elif requeststatus == 3:
                return redirect('commercial_user:denied')
       

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

class AddMoneyFormToSubscribeView(View):
    form_class = AddMoneyNewForm
    template_name = 'commercial_user/addmoneynew.html'

    def get(self, request):
        
        #return render(request, self.template_name, {'form': form})
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
                    commercial_user = {'amount':amount, 'status':subs_paid}
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
                    status = c_user.subscription_paid
                    commercial_user = {'amount':wallet.amount, 'status':status, 'form':form}
                    return render(request, self.template_name, {'commercial_user':commercial_user})
                elif amount is not None and float(amount)>0:
                    wallet.amount += float(amount)
                    wallet.transactions_left -= 1
                    wallet.save()
                    
                    Transaction(sender=current_user, receiver="Admin", amount=amount, timestamp=datetime.now(tz=None)).save()
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
                w_dict['Remaining Transactions'] = wallet.transactions_left

                return render(request, self.template_name, {'wallet': w_dict})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 


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

        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
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

                        return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})
                else:
                    return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied') 

class SendMoneyFormView(View):
    form_class = SendMoneyForm
    template_name = 'commercial_user/sendmoney.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                form = self.form_class(request.user)

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

                            return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})
                        else:
                            form.add_error('amount', "You don't have enough balance.")
                else:
                    return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

class RequestMoneyFormView(View):
    form_class = RequestMoneyForm
    template_name = 'commercial_user/requestmoney.html'

    def get(self, request):
        current_user = request.user
        casual_user = CommercialUser.objects.get(user=current_user)
        if casual_user.statusofrequest == 2:
            if casual_user.subscription_paid == True:
                form = self.form_class(request.user)
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

                            return render(request, 'commercial_user/mywallet.html', {'wallet': w_dict})
                        else:
                            form.add_error('amount', "You have transactions pending. Can't request at this point.")
                else:
                    return render(request, self.template_name, {'form': form})
            else:
                return redirect('commercial_user:addmoneytosubscribe')

        elif casual_user.statusofrequest == 1 or casual_user.statusofrequest == 4: #pending, not validated yet
            return redirect('commercial_user:verifypan')

        else: #if not valid pan, then redirect to another page. Suggest user to sign
        #up for premium or casual user, and redirect to register page
            return redirect('commercial_user:denied')

class LogoutView(View):
    template_name = 'login/login.html'
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('applogin:login'))