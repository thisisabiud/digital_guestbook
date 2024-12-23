from django.shortcuts import render, redirect
from django.views import View
from .models import GuestbookEntry
from .forms import GuestbookEntryForm

class GuestbookView(View):
    template_name = 'guestbook/index.html'
    form_class = GuestbookEntryForm
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        entries = GuestbookEntry.objects.all()[:20]  
        context = {
            'form': form,
            'entries': entries,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('guestbook:index')
            
        entries = GuestbookEntry.objects.all()[:20]  
        context = {
            'form': form,
            'entries': entries,
        }
        return render(request, self.template_name, context)