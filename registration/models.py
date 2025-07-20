from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class Registration(models.Model):
    """Model for storing registration information"""
    
    PAYMENT_TYPE_CHOICES = (
        ('cash', 'پرداخت نقدی'),
        ('installment', 'پرداخت اقساطی'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('failed', 'پرداخت ناموفق'),
    )
    
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=11, verbose_name="شماره تماس")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash', verbose_name="نوع پرداخت")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="وضعیت پرداخت")
    tracking_code = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="کد پیگیری")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت نام")

    
    class Meta:
        verbose_name = "ثبت نام"
        verbose_name_plural = "ثبت نام ها"
        ordering = ['-registration_date']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = get_random_string(10).upper()
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Model for storing payment information"""
    
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='payments', verbose_name="ثبت نام")
    amount = models.IntegerField(verbose_name="مبلغ")
    authority = models.CharField(max_length=100, verbose_name="شناسه پرداخت")
    ref_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه مرجع")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ پرداخت")
    
    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت ها"
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"پرداخت {self.registration.name}"


class Message(models.Model):
    """Model for storing messages sent to users"""
    
    MESSAGE_TYPE_CHOICES = (
        ('sms', 'پیامک'),
        ('email', 'ایمیل'),
    )
    
    MESSAGE_STATUS_CHOICES = (
        ('pending', 'در انتظار ارسال'),
        ('sent', 'ارسال شده'),
        ('failed', 'ارسال ناموفق'),
    )
    
    recipients = models.ManyToManyField(Registration, related_name='messages', verbose_name="دریافت کنندگان")
    subject = models.CharField(max_length=100, blank=True, null=True, verbose_name="موضوع")
    content = models.TextField(verbose_name="متن پیام")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='sms', verbose_name="نوع پیام")
    status = models.CharField(max_length=10, choices=MESSAGE_STATUS_CHOICES, default='pending', verbose_name="وضعیت ارسال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ ارسال")
    
    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"پیام {self.get_message_type_display()} - {self.created_at.strftime('%Y/%m/%d %H:%M')}"
    
    def send(self):
        """Send the message to all recipients"""
        from .sms import SMSNotification
        
        success_count = 0
        failed_count = 0
        
        for recipient in self.recipients.all():
            if self.message_type == 'sms':
                result = SMSNotification.send_custom_message(recipient.phone, self.content)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            # TODO: Implement email sending
        
        if failed_count == 0:
            self.status = 'sent'
            self.sent_at = timezone.now()
        elif success_count > 0:
            self.status = 'partial'
        else:
            self.status = 'failed'
        
        self.save()
