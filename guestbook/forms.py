from django import forms
from django.core.exceptions import ValidationError
from .models import GuestbookEntry, Event
import re

class GuestbookEntryForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name',
            'required': True
        }),
        label='Full Name',
        help_text='Enter your full name (2-100 characters)'
    )
    
    signature_base64 = forms.CharField(widget=forms.HiddenInput())
    
    class Meta:
        model = GuestbookEntry
        fields = ['name', 'signature_base64']
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError('Name is required.')
        
        if len(name) < 2:
            raise ValidationError('Name must be at least 2 characters long.')
        
        if len(name) > 100:
            raise ValidationError('Name must be no more than 100 characters long.')
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError('Name can only contain letters, spaces, hyphens, and apostrophes.')
        
        return name
    
    def clean_signature_base64(self):
        signature = self.cleaned_data.get('signature_base64')
        
        if not signature:
            raise ValidationError('Signature is required.')
        
        # Additional signature validation can be added here if needed
        return signature