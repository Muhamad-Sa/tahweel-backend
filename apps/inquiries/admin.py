from django.contrib import admin

from apps.inquiries.models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "email", "inquiry_type", "status", "created_at"]
    list_filter = ["status", "inquiry_type", "country"]
    search_fields = ["name", "company", "email", "message"]
    autocomplete_fields = ["product"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
