from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
import base64
import re

class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    overlay_image = models.ImageField(upload_to='events', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['date']

class GuestbookEntry(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Full Name"),
        help_text=_("Enter your full name"),
        default="anonymous"  # Default value for name
    )
    signature_base64 = models.TextField(
        verbose_name=_("Signature"),
        help_text=_("Base64 encoded signature image")
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
        
    def clean(self):
        # Validate name
        if not self.name or not self.name.strip():
            raise ValidationError(_('Name is required'))
        
        if len(self.name.strip()) < 2:
            raise ValidationError(_('Name must be at least 2 characters long'))
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", self.name.strip()):
            raise ValidationError(_('Name can only contain letters, spaces, hyphens, and apostrophes'))
        
        # Validate signature
        if self.signature_base64:
            # Validate base64 format and data
            if not re.match(r'^data:image\/(png|jpe?g|webp);base64,', self.signature_base64):
                raise ValidationError(_('Invalid image format'))
                        
            try:
                # Extract and validate base64 data
                base64_str = self.signature_base64.split(',')[1]
                decoded_data = base64.b64decode(base64_str)
                        
                # Check size (max 1MB)
                if len(decoded_data) > 1024 * 1024:
                    raise ValidationError(_('Image too large (max 1MB)'))
            except Exception as e:
                raise ValidationError(f'{_("Invalid image data")}: {str(e)}')
    
    def save(self, *args, **kwargs):
        # Clean the name before saving
        if self.name:
            self.name = self.name.strip()
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Guestbook Entry")
        verbose_name_plural = _("Guestbook Entries")
    
    def __str__(self):
        return f"{self.name} - {_('Entry at')} {self.created_at.strftime('%Y-%m-%d %H:%M')}"