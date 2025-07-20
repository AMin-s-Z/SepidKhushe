import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SMSNotification:
    """
    Utility class for sending SMS notifications via sms.ir
    """
    
    @staticmethod
    def send_sms(mobile, message):
        """
        Send SMS using sms.ir API
        
        Args:
            mobile (str): Mobile number to send SMS to
            message (str): Message to send
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        try:
            api_key = settings.SMS_API_KEY
            line_number = settings.SMS_LINE_NUMBER
            
            url = "https://api.sms.ir/v1/send/bulk"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "lineNumber": line_number,
                "messageText": message,
                "mobiles": [mobile],
                "sendDateTime": None
            }
            
            logger.info(f"Sending SMS to {mobile}: {message}")
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            response_data = response.json()
            
            logger.info(f"SMS API response: {response_data}")
            
            if response.status_code == 200 and response_data.get('status', 0) == 1:
                logger.info(f"SMS sent successfully to {mobile}")
                return True
            else:
                logger.error(f"Failed to send SMS to {mobile}. Response: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
    
    @staticmethod
    def send_registration_success(mobile, name, tracking_code):
        """
        Send registration success SMS
        
        Args:
            mobile (str): Mobile number to send SMS to
            name (str): Name of the user
            tracking_code (str): Registration tracking code
        
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        message = f"{name} عزیز، ثبت نام شما در دوره آموزش پرورش قارچ سپید خوشه نقش جهان با موفقیت انجام شد.\n"
        message += f"کد پیگیری: {tracking_code}\n"
        message += "با تشکر از اعتماد شما"
        
        return SMSNotification.send_sms(mobile, message)
    
    @staticmethod
    def send_payment_success(mobile, name, amount, ref_id):
        """
        Send payment success SMS
        
        Args:
            mobile (str): Mobile number to send SMS to
            name (str): Name of the user
            amount (int): Payment amount
            ref_id (str): Payment reference ID
        
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        message = f"{name} عزیز، پرداخت شما به مبلغ {amount} تومان با موفقیت انجام شد.\n"
        message += f"شناسه پرداخت: {ref_id}\n"
        message += "با تشکر از اعتماد شما"
        message += "آدرس شرکت :  https://maps.app.goo.gl/spgPdd2m4nTKogLv6"
        
        return SMSNotification.send_sms(mobile, message)
    
    @staticmethod
    def send_installment_reminder(mobile, name, amount, due_date):
        """
        Send installment payment reminder SMS
        
        Args:
            mobile (str): Mobile number to send SMS to
            name (str): Name of the user
            amount (int): Payment amount
            due_date (str): Due date for payment
        
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        message = f"{name} عزیز، یادآوری پرداخت قسط دوره آموزش پرورش قارچ به مبلغ {amount} تومان\n"
        message += f"مهلت پرداخت: {due_date}\n"
        message += "سپید خوشه نقش جهان"
        
        return SMSNotification.send_sms(mobile, message)
    
    @staticmethod
    def send_custom_message(mobile, message_text):
        """
        Send custom SMS message
        
        Args:
            mobile (str): Mobile number to send SMS to
            message_text (str): Custom message text
        
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        # Add signature to the message
        message = f"{message_text}\n\nسپید خوشه نقش جهان"
        
        return SMSNotification.send_sms(mobile, message) 