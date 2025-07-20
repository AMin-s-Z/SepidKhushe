from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.crypto import get_random_string
import logging

from .models import Registration, Payment
from .forms import RegistrationForm
from .zarinpal import ZarinPalPayment
from .sms import SMSNotification


class HomeView(View):
    """View for home page"""
    
    def get(self, request):
        """Display home page"""
        return render(request, 'registration/home.html')


class RegistrationView(View):
    """View for registration form"""
    
    def get(self, request):
        """Display registration form"""
        form = RegistrationForm()
        return render(request, 'registration/register.html', {'form': form})
    
    def post(self, request):
        """Process registration form"""
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save registration
            registration = form.save()
            
            # Store registration ID in session
            request.session['registration_id'] = registration.id
            
            # Redirect to payment page
            return redirect('payment')
        
        return render(request, 'registration/register.html', {'form': form})


class PaymentView(View):
    """View for payment page"""
    
    def get(self, request):
        """Display payment page"""
        # Get registration ID from session
        registration_id = request.session.get('registration_id')
        if not registration_id:
            messages.error(request, "اطلاعات ثبت نام یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('register')
        
        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            messages.error(request, "اطلاعات ثبت نام یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('register')
        
        # Set payment amount based on payment type
        if registration.payment_type == 'cash':
            amount = settings.CASH_PAYMENT_AMOUNT
        else:
            amount = settings.INSTALLMENT_FIRST_PAYMENT  # First installment payment
        
        # Check if we're using the mock payment system
        use_mock = getattr(settings, 'USE_MOCK_PAYMENT', False)
        
        if use_mock:
            # Create a mock payment
            payment = Payment.objects.create(
                registration=registration,
                amount=amount,
                authority="MOCK_AUTHORITY_" + get_random_string(16),
                is_paid=False
            )
            
            # Store payment ID in session
            request.session['payment_id'] = payment.id
            
            # Generate mock payment URL
            mock_payment_url = request.build_absolute_uri(reverse('mock_payment'))
            
            # Render the payment page with the mock payment URL
            return render(request, 'registration/payment.html', {
                'registration': registration,
                'payment': payment,
                'payment_url': mock_payment_url
            })
        else:
            # Initialize ZarinPal payment
            zarinpal = ZarinPalPayment()
            
            # Create payment request
            result = zarinpal.payment_request(
                amount=amount,
                description=settings.ZARINPAL_DESCRIPTION,
                mobile=registration.phone,
                callback_url=request.build_absolute_uri(reverse(settings.ZARINPAL_CALLBACK_URL))
            )
            
            if result.Status == 100:
                # Create payment record
                payment = Payment.objects.create(
                    registration=registration,
                    amount=amount,
                    authority=result.Authority
                )
                
                # Store payment ID in session
                request.session['payment_id'] = payment.id
                
                # Render the payment page with the payment URL
                return render(request, 'registration/payment.html', {
                    'registration': registration,
                    'payment': payment,
                    'payment_url': result.URL
                })
            else:
                # Log the error details
                logger = logging.getLogger('registration')
                logger.error(f"ZarinPal error: {result.Message}")
                
                # Show detailed error message in development
                if settings.DEBUG:
                    error_message = f"خطا در اتصال به درگاه پرداخت. کد خطا: {result.Status}. پیام: {result.Message}"
                    messages.error(request, error_message)
                else:
                    # Generic error message in production
                    messages.error(request, "خطا در اتصال به درگاه پرداخت. لطفا با پشتیبانی تماس بگیرید.")
                
                return redirect('payment_error')


class VerifyPaymentView(View):
    """View for verifying payment from ZarinPal"""
    
    def get(self, request):
        """Handle the callback from ZarinPal"""
        authority = request.GET.get('Authority', '')
        status = request.GET.get('Status', '')
        
        # Get registration from session
        registration_id = request.session.get('registration_id')
        if not registration_id:
            messages.error(request, "اطلاعات ثبت نام یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('home')
        
        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            messages.error(request, "اطلاعات ثبت نام یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('home')
        
        # Check if payment was successful
        if status == 'OK':
            # Get payment amount based on payment type
            if registration.payment_type == 'cash':
                amount = settings.CASH_PAYMENT_AMOUNT
            else:
                amount = settings.INSTALLMENT_FIRST_PAYMENT
            
            # Verify payment with ZarinPal
            zarinpal = ZarinPalPayment()
            result = zarinpal.payment_verification(authority, amount)
            
            if result.Status == 100:
                # Payment was successful
                ref_id = result.RefID
                
                # Update registration status
                registration.payment_status = 'paid'
                
                # Generate tracking code if it doesn't exist
                if not registration.tracking_code:
                    registration.tracking_code = get_random_string(10).upper()
                
                registration.save()
                
                # Create payment record
                payment = Payment.objects.create(
                    registration=registration,
                    amount=amount,
                    authority=authority,
                    ref_id=ref_id,
                    is_paid=True,
                    payment_date=timezone.now()
                )
                
                # Send SMS notification
                SMSNotification.send_payment_success(
                    registration.phone,
                    registration.name,
                    amount,
                    ref_id
                )
                
                # Also send registration success SMS with tracking code
                SMSNotification.send_registration_success(
                    registration.phone,
                    registration.name,
                    registration.tracking_code
                )
                
                # Store payment info in session for success page
                request.session['payment_ref_id'] = ref_id
                request.session['payment_tracking_code'] = registration.tracking_code
                
                return redirect('payment_success')
            
            elif result.Status == 101:
                # Payment was successful but already verified
                messages.info(request, "این تراکنش قبلا تایید شده است.")
                return redirect('payment_success')
            
            else:
                # Payment verification failed
                error_message = f"تایید پرداخت با خطا مواجه شد. کد خطا: {result.Status}"
                messages.error(request, error_message)
                
                # Create payment record with failed status
                Payment.objects.create(
                    registration=registration,
                    amount=amount,
                    authority=authority,
                    is_paid=False,
                    payment_date=timezone.now()
                )
                
                return redirect('payment_failed')
        else:
            # Payment was not successful
            messages.error(request, "پرداخت توسط کاربر لغو شد یا با خطا مواجه شد.")
            
            # Get payment amount based on payment type
            if registration.payment_type == 'cash':
                amount = settings.CASH_PAYMENT_AMOUNT
            else:
                amount = settings.INSTALLMENT_FIRST_PAYMENT
                
            # Create payment record with failed status
            Payment.objects.create(
                registration=registration,
                amount=amount,
                authority=authority,
                is_paid=False,
                payment_date=timezone.now()
            )
            
            return redirect('payment_failed')


class TrackRegistrationView(View):
    """View for tracking registration"""
    
    def get(self, request):
        """Display tracking form"""
        tracking_code = request.GET.get('tracking_code')
        
        if tracking_code:
            try:
                registration = Registration.objects.get(tracking_code=tracking_code)
                payments = registration.payments.all().order_by('-payment_date')
                
                return render(request, 'registration/track_result.html', {
                    'registration': registration,
                    'payments': payments,
                })
            except Registration.DoesNotExist:
                messages.error(request, "کد پیگیری وارد شده معتبر نیست.")
        
        return render(request, 'registration/track.html')
    
    def post(self, request):
        """Process tracking form"""
        phone = request.POST.get('phone')
        
        if phone:
            # Change created_at to registration_date
            registrations = Registration.objects.filter(phone=phone).order_by('-registration_date')
            
            if registrations.exists():
                return render(request, 'registration/track_result.html', {
                    'registrations': registrations,
                })
            else:
                messages.error(request, "شماره تلفن وارد شده در سیستم ثبت نشده است.")
        else:
            messages.error(request, "لطفا شماره تلفن خود را وارد کنید.")
        
        return render(request, 'registration/track.html')


class PaymentSuccessView(View):
    """View for payment success page"""
    
    def get(self, request):
        """Display payment success page"""
        # Get payment info from session
        payment_ref_id = request.session.get('payment_ref_id')
        payment_tracking_code = request.session.get('payment_tracking_code')
        
        if not payment_ref_id:
            messages.error(request, "اطلاعات پرداخت یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('home')
        
        # Get registration and payment info
        try:
            payment = Payment.objects.get(ref_id=payment_ref_id)
            registration = payment.registration
        except (Payment.DoesNotExist, Registration.DoesNotExist):
            messages.error(request, "اطلاعات پرداخت یافت نشد. لطفا مجددا تلاش کنید.")
            return redirect('home')
        
        # Clear session data
        if 'registration_id' in request.session:
            del request.session['registration_id']
        if 'payment_ref_id' in request.session:
            del request.session['payment_ref_id']
        if 'payment_tracking_code' in request.session:
            del request.session['payment_tracking_code']
        
        return render(request, 'registration/payment_success.html', {
            'registration': registration,
            'payment': payment
        })


class PaymentFailedView(View):
    """View for payment failed page"""
    
    def get(self, request):
        """Display payment failed page"""
        # Get registration ID from session
        registration_id = request.session.get('registration_id')
        
        if registration_id:
            try:
                registration = Registration.objects.get(id=registration_id)
            except Registration.DoesNotExist:
                registration = None
        else:
            registration = None
        
        return render(request, 'registration/payment_failed.html', {
            'registration': registration
        })


class PaymentErrorView(View):
    """View for payment error page"""
    
    def get(self, request):
        """Display payment error page"""
        # Get registration ID from session
        registration_id = request.session.get('registration_id')
        
        if registration_id:
            try:
                registration = Registration.objects.get(id=registration_id)
            except Registration.DoesNotExist:
                registration = None
        else:
            registration = None
        
        return render(request, 'registration/payment_error.html', {
            'registration': registration
        })


class MockPaymentView(View):
    """Mock payment gateway for testing"""
    
    def get(self, request):
        """Display mock payment page"""
        payment_id = request.session.get('payment_id')
        if not payment_id:
            messages.error(request, "اطلاعات پرداخت یافت نشد.")
            return redirect('register')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            registration = payment.registration
        except (Payment.DoesNotExist, Registration.DoesNotExist):
            messages.error(request, "اطلاعات پرداخت یافت نشد.")
            return redirect('register')
        
        return render(request, 'registration/mock_payment.html', {
            'payment': payment,
            'registration': registration
        })
    
    def post(self, request):
        """Process mock payment"""
        payment_id = request.session.get('payment_id')
        if not payment_id:
            messages.error(request, "اطلاعات پرداخت یافت نشد.")
            return redirect('home')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            registration = payment.registration
        except (Payment.DoesNotExist, Registration.DoesNotExist):
            messages.error(request, "اطلاعات پرداخت یافت نشد.")
            return redirect('home')
        
        # Get payment status from form
        payment_status = request.POST.get('payment_status', 'failed')
        
        if payment_status == 'success':
            # Update payment record
            payment.is_paid = True
            payment.ref_id = "MOCK_REF_" + get_random_string(8)
            payment.payment_date = timezone.now()
            payment.save()
            
            # Update registration status
            registration.payment_status = 'paid'
            
            # Generate tracking code if it doesn't exist
            if not registration.tracking_code:
                registration.tracking_code = get_random_string(10).upper()
            
            registration.save()
            
            # Store payment info in session for success page
            request.session['payment_ref_id'] = payment.ref_id
            request.session['payment_tracking_code'] = registration.tracking_code
            
            # Send SMS notification if enabled
            if getattr(settings, 'SEND_SMS_NOTIFICATIONS', False):
                SMSNotification.send_payment_success(
                    registration.phone,
                    registration.name,
                    payment.amount,
                    payment.ref_id
                )
                
                # Also send registration success SMS with tracking code
                SMSNotification.send_registration_success(
                    registration.phone,
                    registration.name,
                    registration.tracking_code
                )
            
            return redirect('payment_success')
        else:
            # Update payment record with failed status
            payment.is_paid = False
            payment.payment_date = timezone.now()
            payment.save()
            
            return redirect('payment_failed')
