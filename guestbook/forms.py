from django import forms
from django.core.exceptions import ValidationError
from .models import GuestbookEntry, Event

class GuestbookEntryForm(forms.ModelForm):
    signature_base64 = forms.CharField(widget=forms.HiddenInput())
    
    class Meta:
        model = GuestbookEntry
        fields = ['signature_base64']