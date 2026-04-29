import urllib.request
import urllib.error
import json
from src.constants import KONNECT_WALLET_ID, KONNECT_API_KEY, KONNECT_INIT_URL, KONNECT_STATUS_URL

def init_payment(amount=2000):
    """
    Initializes a payment session with Konnect.
    Returns (pay_url, payment_ref) or (None, None) on error.
    """
    payload = {
        "receiverWalletId": KONNECT_WALLET_ID,
        "token": "TND",
        "amount": amount,
        "type": "immediate",
        "description": "Neon Drift Unlock",
        "lifespan": 10,
        "checkoutForm": False,
        "addPaymentFeesToAmount": True,
        "firstName": "Player",
        "lastName": "One",
        "phoneNumber": "22222222",
        "email": "player@neondrift.local",
        "orderId": "unlock_neon_drift"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(KONNECT_INIT_URL, data=data, method='POST')
    req.add_header('x-api-key', KONNECT_API_KEY)
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get('payUrl'), res_data.get('paymentRef')
    except urllib.error.URLError as e:
        print("Payment init error:", e)
        return None, None

def check_payment_status(payment_ref):
    """
    Checks the status of the payment.
    Returns True if completed, False otherwise.
    """
    url = KONNECT_STATUS_URL + payment_ref
    req = urllib.request.Request(url, method='GET')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            status = res_data.get('payment', {}).get('status')
            return status == 'completed'
    except urllib.error.URLError as e:
        print("Payment status error:", e)
        return False
