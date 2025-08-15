import re
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView
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

@method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
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

@method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
class EventsView(View):
    template_name = 'guestbook/event.html'
    items_per_page = 9 

    def get(self, request, *args, **kwargs):
        event_list = Event.objects.all().order_by('-date')
        
        paginator = Paginator(event_list, self.items_per_page)
        page = request.GET.get('page', 1)

        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            events = paginator.page(1)
        except EmptyPage:
            events = paginator.page(paginator.num_pages)

        # Calculate pagination range with ellipsis
        page_range = events.paginator.get_elided_page_range(
            events.number,
            on_each_side=2,
            on_ends=1
        )

        context = {
            'events': events,
            'page_range': page_range,
        }
        return render(request, self.template_name, context)

@method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
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
    
    def _notify_new_message(self, entry, event_id):
        """Notify connected WebSocket clients of new message"""
        channel_layer = get_channel_layer()

        # Prepare message data
        message_data = {
            'id': entry.id,
            'name': entry.name,
            'signature_base64': entry.signature_base64,
            'created_at': entry.created_at.strftime('%b %d, %Y %I:%M %p'),
            'event_id': event_id
        }

        # Send to appropriate group based on event_id
        group_name = f'guestbook_{event_id}' if event_id else 'guestbook_all'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'message_update',
                'message': message_data
            }
        )
    
    def post(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        
        form = self.form_class(request.POST)
        
        try:
            if form.is_valid():
                entry = form.save(commit=False)
                entry.event = event
                
                # Get the cleaned data
                name = form.cleaned_data.get('name')
                signature = form.cleaned_data.get('signature_base64')
                
                if name:
                    entry.name = name.strip()
                
                # Validate and save base64 signature
                if signature:
                    # Validate base64 format with comprehensive checks
                    if not re.match(r'^data:image\/(png|jpe?g|webp);base64,', signature):
                        raise ValidationError('Invalid image format')
                    
                    try:
                        # Extract and validate base64 data
                        base64_data = signature.split(',')[1]
                        decoded_data = base64.b64decode(base64_data)
                        
                        # Size validation (max 1MB)
                        if len(decoded_data) > 1024 * 1024:
                            raise ValidationError('Image too large (max 1MB)')
                        
                        entry.signature_base64 = signature
                    except Exception as e:
                        raise ValidationError(f'Invalid image data: {str(e)}')
                
                entry.save()
                # Notify WebSocket clients
                self._notify_new_message(entry, event_id)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Thank you {entry.name} for signing our guestbook!',
                    'redirect_url': reverse('guestbook:write_message', kwargs={'event_id': event_id}) if event_id else reverse('guestbook:messages_display', kwargs={'event_id': 1})  # Use a default event_id if needed
                })
            else:
                # Return form validation errors
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        if field == '__all__':
                            errors.append(error)
                        else:
                            field_name = form.fields[field].label or field.replace('_', ' ').title()
                            errors.append(f"{field_name}: {error}")
                
                return JsonResponse({
                    'status': 'error',
                    'errors': errors,
                    'message': 'Please correct the errors below.'
                }, status=400)
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'An unexpected error occurred: {str(e)}'
            }, status=500)

@method_decorator(login_required(login_url='guestbook:login'), name='dispatch')   
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

# @login_required(login_url='guestbook:login')  
# def dynamic(request, event_id):
#     event = get_object_or_404(Event, pk=event_id)
#     messages = event.entries.all().order_by('-created_at')
#     context = {
#         'messages': messages,
#     }
#     return render(request, 'guestbook/dynamic.html', context)

@method_decorator(login_required(login_url='guestbook:login'), name='dispatch')
class MessageDisplayView(TemplateView):
    template_name = 'guestbook/messages_template.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get event_id from URL if it exists
        event_id = self.kwargs.get('event_id')
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        
        # Query messages
        messages = GuestbookEntry.objects.filter(event=event) if event else GuestbookEntry.objects.all()
        messages = messages.order_by('-created_at')
        
        # Add to context
        context.update({
            'messages': messages,
            'event': event,
            'ws_protocol': 'wss' if self.request.is_secure() else 'ws',
            'host': self.request.get_host(),
        })
        
        return context