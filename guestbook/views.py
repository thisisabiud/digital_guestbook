import re
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.utils import timezone
import base64
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from guestbook.forms import GuestbookEntryForm

from .models import GuestbookEntry, Event
from django.contrib.auth import authenticate, login, logout

class EventSearchView(View):
    def get(self, request):
        try:
            query = request.GET.get('q', '').strip()
            if len(query) < 2:
                return JsonResponse({'events': []})
            
            events = Event.objects.filter(
                Q(name__icontains=query) |
                Q(location__icontains=query)
            ).order_by('date')
            
            now = timezone.now()
            
            data = [{
                'id': event.id,
                'name': event.name,
                'date': event.date.strftime('%Y-%m-%d'),
                'location': event.location,
                'status': 'past' if event.date < now.date() else 'today' if event.date == now.date() else 'upcoming',
                'created_at': event.created_at.strftime('%b %d, %Y'),
                'updated_at': event.updated_at.strftime('%b %d, %Y')
            } for event in events]
            
            return JsonResponse({'events': data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
# @method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully')
        return redirect('guestbook:login')
    
class LoginView(View):
    template_name = 'guestbook/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('guestbook:events')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('guestbook:events')
        
        messages.error(request, 'Invalid username or password')
        return render(request, self.template_name)

# @method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
class EventsView(View):
    template_name = 'guestbook/event.html'
    
    def get(self, request, *args, **kwargs):
        events = Event.objects.all().order_by('date')

        context = {
            'events': events,
        }
        return render(request, self.template_name, context)

# @method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
class GuestbookView(View):

    template_name = 'guestbook/index.html'
    form_class = GuestbookEntryForm
    entries_per_page = 20
    
    def get(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        
        form = self.form_class(initial={'event': event}) if event else self.form_class()

        entries = GuestbookEntry.objects.filter(event=event) if event else GuestbookEntry.objects.all()
        entries = entries.order_by('-created_at')
        
        paginator = Paginator(entries, self.entries_per_page)
        page_number = request.GET.get('page', 1)
        
        context = {
            'form': form,
            'entries': paginator.get_page(page_number),
            'event': event,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        
        form = self.form_class(request.POST)
        
        try:
            if form.is_valid():
                entry = form.save(commit=False)
                entry.event = event
                
                # Validate and save base64 signature
                signature = form.cleaned_data.get('signature')
                if signature:
                    # Validate base64 format with comprehensive checks
                    if not re.match(r'^data:image\/(png|jpe?g|webp);base64,', signature):
                        raise ValidationError('Invalid image format')
                    
                    try:
                        # Extract and validate base64 data
                        base64_data = signature.split(',')[1]
                        decoded_data = base64.b64decode(base64_data)
                        
                        print(decoded_data)
                        # Size validation (max 1MB)
                        if len(decoded_data) > 1024 * 1024:
                            raise ValidationError('Image too large (max 1MB)')
                        
                        entry.signature_base64 = signature
                    except Exception as e:
                        raise ValidationError(f'Invalid image data: {str(e)}')
                
                entry.save()
                
                messages.success(request, 'Thank you for signing our guestbook!')
                return redirect('guestbook:message', event_id=event_id)
            
        except ValidationError as e:
            messages.error(request, str(e))
        
        context = {
            'form': form,
            'event': event,
        }
        return render(request, self.template_name, context)

# @method_decorator(login_required(login_url='guestbook:login'), name='dispatch')   
class MessagesView(View):
    template_name = 'guestbook/messages.html'
    
    def get(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        messages = event.entries.all().order_by('-created_at')
        context = {
            'event': event,
            'messages': messages,
        }
        return render(request, self.template_name, context)