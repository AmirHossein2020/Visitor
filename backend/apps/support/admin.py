from django.contrib import admin
from .models import SupportAttachment, SupportMessage, SupportTicket

admin.site.register((SupportTicket, SupportMessage, SupportAttachment))
