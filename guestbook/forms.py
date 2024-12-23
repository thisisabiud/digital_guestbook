from django import forms
from .models import GuestbookEntry
import base64
import uuid
from django.core.files.base import ContentFile

class GuestbookEntryForm(forms.ModelForm):
    signature = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = GuestbookEntry
        fields = ['name', 'signature_image', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 transition duration-200'
                }),
            'message': forms.Textarea(attrs={
                'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 transition duration-200'
                }),
            'signature_image': forms.HiddenInput(),
        }

    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if not signature:
            raise forms.ValidationError("Signature is required")
        return signature

    def save(self, commit=True):
        # Decode base64 image
        signature_data = self.cleaned_data.get('signature')
        if signature_data and 'base64' in signature_data:
            # Remove header
            header, data = signature_data.split(',', 1)
            
            # Decode base64
            image_data = base64.b64decode(data)
            
            # Generate filename
            filename = f"{uuid.uuid4()}.png"
            
            # Create ContentFile from image data
            image_file = ContentFile(image_data)
            
            # Set signature_image
            self.instance.signature_image.save(filename, image_file, save=False)
        
        return super().save(commit)