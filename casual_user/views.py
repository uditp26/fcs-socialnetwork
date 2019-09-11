from django.shortcuts import render
from django.views.generic import View
from django.http import Http404

# Create your views here.
class HomepageView(View):
    template_name = 'casual_user/homepage.html'

    def get(self, request):
        current_user = request.user
        if str(current_user) is 'AnonymousUser':
            raise Http404
        else:
            return render(request, self.template_name, {'current_user': current_user})
            