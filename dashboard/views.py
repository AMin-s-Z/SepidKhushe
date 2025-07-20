from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from registration.models import Registration, Payment, Message
from registration.sms import SMSNotification

class DashboardView(LoginRequiredMixin, View):
    """Dashboard home view"""
    
    def get(self, request):
        """Display dashboard home"""
        # Get counts for dashboard
        total_registrations = Registration.objects.count()
        paid_registrations = Registration.objects.filter(payment_status='paid').count()
        pending_registrations = Registration.objects.filter(payment_status='pending').count()
        failed_registrations = Registration.objects.filter(payment_status='failed').count()
        
        # Get latest registrations
        latest_registrations = Registration.objects.all()[:10]
        
        # Get latest payments
        latest_payments = Payment.objects.filter(is_paid=True).order_by('-payment_date')[:10]
        
        context = {
            'total_registrations': total_registrations,
            'paid_registrations': paid_registrations,
            'pending_registrations': pending_registrations,
            'failed_registrations': failed_registrations,
            'latest_registrations': latest_registrations,
            'latest_payments': latest_payments,
        }
        
        return render(request, 'dashboard/index.html', context)


class RegistrationListView(LoginRequiredMixin, View):
    """View for listing registrations"""
    
    def get(self, request):
        """Display registration list"""
        # Get filter parameters
        payment_type = request.GET.get('payment_type', '')
        payment_status = request.GET.get('payment_status', '')
        search_query = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Start with all registrations
        registrations = Registration.objects.all()
        
        # Apply filters
        if payment_type:
            registrations = registrations.filter(payment_type=payment_type)
        
        if payment_status:
            registrations = registrations.filter(payment_status=payment_status)
        
        if search_query:
            registrations = registrations.filter(
                Q(name__icontains=search_query) | 
                Q(phone__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(tracking_code__icontains=search_query)
            )
        
        if date_from:
            try:
                date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                registrations = registrations.filter(registration_date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
                registrations = registrations.filter(registration_date__lte=date_to)
            except ValueError:
                pass
        
        context = {
            'registrations': registrations,
            'payment_type': payment_type,
            'payment_status': payment_status,
            'search_query': search_query,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return render(request, 'dashboard/registrations.html', context)


class RegistrationDetailView(LoginRequiredMixin, View):
    """View for registration details"""
    
    def get(self, request, pk):
        """Display registration details"""
        registration = get_object_or_404(Registration, pk=pk)
        payments = registration.payments.all().order_by('-payment_date')
        
        context = {
            'registration': registration,
            'payments': payments,
        }
        
        return render(request, 'dashboard/registration_detail.html', context)


class PaymentListView(LoginRequiredMixin, View):
    """View for listing payments"""
    
    def get(self, request):
        """Display payment list"""
        # Get filter parameters
        payment_status = request.GET.get('payment_status', '')
        search_query = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Start with all payments
        payments = Payment.objects.all()
        
        # Apply filters
        if payment_status:
            if payment_status == 'paid':
                payments = payments.filter(is_paid=True)
            elif payment_status == 'unpaid':
                payments = payments.filter(is_paid=False)
        
        if search_query:
            payments = payments.filter(
                Q(registration__name__icontains=search_query) | 
                Q(registration__phone__icontains=search_query) | 
                Q(ref_id__icontains=search_query) |
                Q(authority__icontains=search_query)
            )
        
        if date_from:
            try:
                date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                payments = payments.filter(payment_date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
                payments = payments.filter(payment_date__lte=date_to)
            except ValueError:
                pass
        
        context = {
            'payments': payments,
            'payment_status': payment_status,
            'search_query': search_query,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return render(request, 'dashboard/payment_list.html', context)


class MessageListView(LoginRequiredMixin, View):
    """View for listing messages"""
    
    def get(self, request):
        """Display message list"""
        messages_list = Message.objects.all().order_by('-created_at')
        
        context = {
            'messages_list': messages_list,
        }
        
        return render(request, 'dashboard/messages.html', context)


class MessageCreateView(LoginRequiredMixin, View):
    """View for creating messages"""
    
    def get(self, request):
        """Display message creation form"""
        # Get filter parameters for selecting recipients
        payment_type = request.GET.get('payment_type', '')
        payment_status = request.GET.get('payment_status', '')
        search_query = request.GET.get('search', '')
        
        # Start with all registrations
        registrations = Registration.objects.all()
        
        # Apply filters
        if payment_type:
            registrations = registrations.filter(payment_type=payment_type)
        
        if payment_status:
            registrations = registrations.filter(payment_status=payment_status)
        
        if search_query:
            registrations = registrations.filter(
                Q(name__icontains=search_query) | 
                Q(phone__icontains=search_query) | 
                Q(email__icontains=search_query)
            )
        
        context = {
            'registrations': registrations,
            'payment_type': payment_type,
            'payment_status': payment_status,
            'search_query': search_query,
        }
        
        return render(request, 'dashboard/message_create.html', context)
    
    def post(self, request):
        """Process message creation form"""
        # Get message data
        recipient_ids = request.POST.getlist('recipients')
        subject = request.POST.get('subject', '')
        content = request.POST.get('content', '')
        message_type = request.POST.get('message_type', 'sms')
        
        if not recipient_ids:
            messages.error(request, "لطفا حداقل یک دریافت کننده انتخاب کنید.")
            return redirect('dashboard:message_create')
        
        if not content:
            messages.error(request, "لطفا متن پیام را وارد کنید.")
            return redirect('dashboard:message_create')
        
        # Create message
        message = Message.objects.create(
            subject=subject,
            content=content,
            message_type=message_type
        )
        
        # Add recipients
        for recipient_id in recipient_ids:
            try:
                registration = Registration.objects.get(id=recipient_id)
                message.recipients.add(registration)
            except Registration.DoesNotExist:
                pass
        
        # Send message
        message.send()
        
        messages.success(request, "پیام با موفقیت ارسال شد.")
        return redirect('dashboard:messages')


class MessageDetailView(LoginRequiredMixin, View):
    """View for message details"""
    
    def get(self, request, pk):
        """Display message details"""
        message = get_object_or_404(Message, pk=pk)
        recipients = message.recipients.all()
        
        context = {
            'message': message,
            'recipients': recipients,
        }
        
        return render(request, 'dashboard/message_detail.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class BulkActionView(LoginRequiredMixin, View):
    """View for bulk actions on registrations"""
    
    def post(self, request):
        """Process bulk action"""
        action = request.POST.get('action', '')
        registration_ids = request.POST.getlist('registration_ids', [])
        
        if not action or not registration_ids:
            return JsonResponse({'success': False, 'message': 'پارامترهای ناقص'})
        
        # Get registrations
        registrations = Registration.objects.filter(id__in=registration_ids)
        
        if action == 'send_message':
            # Redirect to message create with pre-selected recipients
            recipient_ids = ','.join(registration_ids)
            return JsonResponse({'success': True, 'redirect': f'/dashboard/messages/create/?recipients={recipient_ids}'})
        
        elif action == 'update_status':
            new_status = request.POST.get('new_status', '')
            if not new_status:
                return JsonResponse({'success': False, 'message': 'وضعیت جدید مشخص نشده است'})
            
            # Update status
            registrations.update(payment_status=new_status)
            return JsonResponse({'success': True, 'message': f'وضعیت {registrations.count()} ثبت نام با موفقیت بروزرسانی شد'})
        
        return JsonResponse({'success': False, 'message': 'عملیات نامعتبر'})
