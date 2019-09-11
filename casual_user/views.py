from django.shortcuts import render
from django.views.generic import View
from django.http import Http404
from .models import CasualUser

class HomepageView(View):
    template_name = 'casual_user/homepage.html'

    def get(self, request):
        current_user = request.user
        print(type(current_user))
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            casual_user = CasualUser.objects.get(user=current_user)
            bundle = dict()
            name = casual_user.user.first_name + ' ' +  casual_user.user.last_name
            bundle = {'name': name, 'date_of_birth': casual_user.date_of_birth, 'gender': casual_user.gender,'phone': casual_user.phone}
            return render(request, self.template_name, {'current_user':bundle})
            