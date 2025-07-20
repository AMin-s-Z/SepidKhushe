import json
import requests
import logging
from dataclasses import dataclass
from django.conf import settings

logger = logging.getLogger(__name__)

@dataclass
class ZarinpalResponse:
    """Response from ZarinPal API"""
    Status: int
    Authority: str = ""
    URL: str = ""
    RefID: str = ""
    Message: str = ""

class ZarinPalPayment:
    """
    Utility class for ZarinPal payment gateway integration
    """
    
    def __init__(self):
        """Initialize ZarinPal payment gateway"""
        self.sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        
        # Set the appropriate endpoints and merchant ID based on sandbox mode
        if self.sandbox:
            # Use test merchant ID for sandbox
            self.merchant_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay/"
            self.request_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.verify_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
        else:
            # Use actual merchant ID for production
            self.merchant_id = settings.ZARINPAL_MERCHANT_ID
            self.payment_url = "https://www.zarinpal.com/pg/StartPay/"
            self.request_url = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.verify_url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        
        logger.info(f"ZarinPal initialized with sandbox={self.sandbox}, merchant_id={self.merchant_id}")
    
    def payment_request(self, amount, description, callback_url, email=None, mobile=None):
        """
        Request a payment from ZarinPal
        
        Args:
            amount (int): Payment amount in Tomans
            description (str): Payment description
            callback_url (str): Callback URL after payment
            email (str, optional): User's email
            mobile (str, optional): User's mobile number
        
        Returns:
            ZarinpalResponse: Response from ZarinPal API
        """
        try:
            # Prepare the request data
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount,
                "description": description,
                "callback_url": callback_url
            }
            
            if email:
                data["email"] = email
            if mobile:
                data["mobile"] = mobile
            
            # For production, use metadata format
            if not self.sandbox:
                metadata = {}
                if email:
                    metadata["email"] = email
                if mobile:
                    metadata["mobile"] = mobile
                
                if metadata:
                    data["metadata"] = metadata
            
            logger.info(f"ZarinPal payment request data: {data}")
            logger.info(f"ZarinPal payment request URL: {self.request_url}")
            
            # Send the request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(self.request_url, json=data, headers=headers, timeout=10)
            response_data = response.text
            logger.info(f"ZarinPal payment request response: {response_data}")
            
            # Parse the response
            result = json.loads(response_data)
            
            # Handle the response based on sandbox mode
            if self.sandbox:
                if 'Status' in result and result['Status'] == 100:
                    return ZarinpalResponse(
                        Status=result['Status'],
                        Authority=result['Authority'],
                        URL=f"{self.payment_url}{result['Authority']}"
                    )
                else:
                    status = result.get('Status', 0)
                    return ZarinpalResponse(Status=status, Message=f"Failed to create payment: {result}")
            else:
                if 'data' in result and 'code' in result['data'] and result['data']['code'] == 100:
                    return ZarinpalResponse(
                        Status=result['data']['code'],
                        Authority=result['data']['authority'],
                        URL=f"{self.payment_url}{result['data']['authority']}"
                    )
                else:
                    status = result.get('data', {}).get('code', 0)
                    return ZarinpalResponse(Status=status, Message=f"Failed to create payment: {result}")
            
        except Exception as e:
            logger.error(f"Error in ZarinPal payment request: {str(e)}")
            return ZarinpalResponse(Status=0, Message=str(e))
    
    def payment_verification(self, authority, amount):
        """
        Verify a payment from ZarinPal
        
        Args:
            authority (str): Payment authority
            amount (int): Payment amount in Tomans
        
        Returns:
            ZarinpalResponse: Response from ZarinPal API
        """
        try:
            # Prepare the request data
            data = {
                "merchant_id": self.merchant_id,
                "authority": authority,
                "amount": amount
            }
            
            logger.info(f"ZarinPal verification request data: {data}")
            logger.info(f"ZarinPal verification URL: {self.verify_url}")
            
            # Send the request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(self.verify_url, json=data, headers=headers, timeout=10)
            response_data = response.text
            logger.info(f"ZarinPal verification response: {response_data}")
            
            # Parse the response
            result = json.loads(response_data)
            
            # Handle the response based on sandbox mode
            if self.sandbox:
                if 'Status' in result:
                    ref_id = result.get('RefID', '')
                    return ZarinpalResponse(Status=result['Status'], RefID=ref_id)
                else:
                    status = result.get('Status', 0)
                    return ZarinpalResponse(Status=status, Message=f"Failed to verify payment: {result}")
            else:
                if 'data' in result and 'code' in result['data']:
                    ref_id = result['data'].get('ref_id', '')
                    return ZarinpalResponse(Status=result['data']['code'], RefID=ref_id)
                else:
                    status = result.get('data', {}).get('code', 0)
                    return ZarinpalResponse(Status=status, Message=f"Failed to verify payment: {result}")
            
        except Exception as e:
            logger.error(f"Error in ZarinPal payment verification: {str(e)}")
            return ZarinpalResponse(Status=0, Message=str(e)) 