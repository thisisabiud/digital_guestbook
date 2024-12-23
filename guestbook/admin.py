from django.contrib import admin
from .models import GuestbookEntry

@admin.register(GuestbookEntry)
class GuestbookEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'message', 'created_at')
    search_fields = ('name', 'message')
    list_filter = ('created_at',)
    readonly_fields = ('signature_image',)