from django.contrib import admin
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import GuestbookEntry, Event

@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'created_at', 'signature_preview')
    list_filter = ('event', 'created_at')
    readonly_fields = ('signature_preview', 'created_at')
    search_fields = ('name', 'event__name')

    def signature_preview(self, obj):
        if obj.signature_base64:
            return mark_safe(f'<img src="{obj.signature_base64}" style="max-width:200px; max-height:100px;"/>')
        return _('No signature')
    signature_preview.short_description = _('Signature Preview')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'overlay_image_preview', 'entries_count', 'created_at', 'updated_at')
    list_filter = ('date', 'created_at')
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'updated_at', 'overlay_image_preview')

    def entries_count(self, obj):
        return obj.entries.count()
    entries_count.short_description = _('Entries')

    def overlay_image_preview(self, obj):
        if obj.overlay_image:
            return mark_safe(f'<img src="{obj.overlay_image.url}" style="max-width:100px; max-height:100px;"/>')
        return _('No image')
    overlay_image_preview.short_description = _('Overlay Image Preview')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('entries')