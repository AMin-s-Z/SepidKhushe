from django.contrib import admin
from .models import Registration, Payment, Message


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone',  'payment_type', 'payment_status', 'tracking_code', 'registration_date')
    list_filter = ('payment_type', 'payment_status', 'registration_date')
    search_fields = ('name', 'phone', 'email', 'tracking_code')
    readonly_fields = ('registration_date',)
    ordering = ('-registration_date',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('registration', 'amount', 'is_paid', 'payment_date', 'ref_id')
    list_filter = ('is_paid', 'payment_date')
    search_fields = ('registration__name', 'registration__phone', 'ref_id', 'authority')
    readonly_fields = ('payment_date',)
    ordering = ('-payment_date',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'message_type', 'status', 'created_at', 'sent_at')
    list_filter = ('message_type', 'status', 'created_at')
    search_fields = ('subject', 'content')
    readonly_fields = ('created_at', 'sent_at')
    filter_horizontal = ('recipients',)
    ordering = ('-created_at',)
