from django.urls import path
from .views import (
    HomeView, RegistrationView, PaymentView, VerifyPaymentView,
    PaymentSuccessView, PaymentFailedView, PaymentErrorView,
    TrackRegistrationView, MockPaymentView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify'),
    path('payment/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failed/', PaymentFailedView.as_view(), name='payment_failed'),
    path('payment/error/', PaymentErrorView.as_view(), name='payment_error'),
    path('track/', TrackRegistrationView.as_view(), name='track'),
    path('mock-payment/', MockPaymentView.as_view(), name='mock_payment'),
] 