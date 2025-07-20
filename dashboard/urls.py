from django.urls import path
from .views import (
    DashboardView, RegistrationListView, RegistrationDetailView,
    PaymentListView, MessageListView, MessageCreateView, 
    MessageDetailView, BulkActionView
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('registrations/', RegistrationListView.as_view(), name='registrations'),
    path('registrations/<int:pk>/', RegistrationDetailView.as_view(), name='registration_detail'),
    path('payments/', PaymentListView.as_view(), name='payments'),
    path('messages/', MessageListView.as_view(), name='messages'),
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('bulk-action/', BulkActionView.as_view(), name='bulk_action'),
] 