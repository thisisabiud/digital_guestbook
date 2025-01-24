from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
import base64
import re

class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['date']

class GuestbookEntry(models.Model):
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
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Guestbook Entry")
        verbose_name_plural = _("Guestbook Entries")

    def __str__(self):
        return f"{_('Entry at')} {self.created_at.strftime('%Y-%m-%d %H:%M')}"