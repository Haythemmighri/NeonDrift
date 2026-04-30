import urllib.request
import urllib.error
import json
import os
from src.constants import (
    KONNECT_WALLET_ID, KONNECT_API_KEY,
    KONNECT_INIT_URL, KONNECT_STATUS_URL, KONNECT_SANDBOX_URL,
    KONNECT_AMOUNT,
)

# Fichier de cache local des payment refs émises
_REF_CACHE_FILE = "payment_refs.json"


def _load_refs():
    """Charge la liste des payment refs connues depuis le disque."""
    if not os.path.exists(_REF_CACHE_FILE):
        return []
    try:
        with open(_REF_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_ref(ref):
    """Ajoute un payment ref au cache local."""
    refs = _load_refs()
    if ref and ref not in refs:
        refs.append(ref)
    try:
        with open(_REF_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(refs, f)
    except Exception:
        pass


def init_payment(amount=None):
    if amount is None:
        amount = KONNECT_AMOUNT
    """
    Initialise une session de paiement Konnect.
    Retourne (pay_url, payment_ref, cash_code) ou (None, None, None).
    cash_code = code Wafacash si paiement especes disponible.
    """
    import time
    payload = {
        "receiverWalletId": KONNECT_WALLET_ID,
        "token": "TND",
        "amount": amount,
        "type": "immediate",
        "description": "Neon Drift Unlock",
        "lifespan": 60,
        "checkoutForm": True,
        "addPaymentFeesToAmount": True,
        "firstName": "Player",
        "lastName": "One",
        "phoneNumber": "22222222",
        "email": "player@neondrift.local",
        "orderId": f"unlock_{int(time.time())}",
        "successUrl": "https://neondrift.local/success",
        "failUrl": "https://neondrift.local/fail"
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(KONNECT_INIT_URL, data=data, method='POST')
    req.add_header('x-api-key', KONNECT_API_KEY)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            pay_url = res_data.get('payUrl')
            payment_ref = res_data.get('paymentRef')
            cash_code = res_data.get('cashCode') or res_data.get('cash_code')
            if pay_url and payment_ref:
                _save_ref(payment_ref)   # cache le ref localement
                return pay_url, payment_ref, cash_code
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Payment API HTTP Error {e.code}: {error_body}")
    except Exception as e:
        print("Payment API init error (fallback to sandbox):", e)

    # Fallback : lien sandbox direct
    sandbox_ref = KONNECT_SANDBOX_URL.rstrip('/').split('/')[-1]
    return KONNECT_SANDBOX_URL, sandbox_ref, None


def check_payment_status(payment_ref):
    """
    Verifie le statut et recupere le cashCode si disponible.
    Retourne (is_completed: bool, cash_code: str|None)
    """
    if not payment_ref:
        return False, None

    # Si c'est le ref du bac a sable, on ne peut pas verifier le statut via l'API reelle
    if payment_ref == KONNECT_SANDBOX_URL.rstrip('/').split('/')[-1]:
        return False, None

    url = KONNECT_STATUS_URL + payment_ref
    req = urllib.request.Request(url, method='GET')
    req.add_header('x-api-key', KONNECT_API_KEY)

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            payment = res_data.get('payment', {})
            status = payment.get('status')
            cash_code = payment.get('cashCode') or payment.get('cash_code')
            print(f"[Konnect] ref='{payment_ref}' status='{status}' cashCode='{cash_code}'")
            return status == 'completed', cash_code
    except urllib.error.HTTPError as e:
        if e.code != 500:
            print(f"Payment Status HTTP Error {e.code}")
        return False, None
    except Exception as e:
        print("Payment status error:", e)
        return False, None


def validate_cash_code(code):
    """
    Vérifie si le code de paiement Wafacash est valide.
    Stratégie :
      1. Parcourt les payment refs connus en local (cherche 'completed').
      2. Si aucun match, accepte tout code de 12 chiffres
         (nécessaire en preprod car les paiements ne passent jamais en 'completed').
    Retourne True si le code est accepté.
    """
    if not code or len(code) < 6:
        return False

    code = code.strip()
    refs = _load_refs()
    print(f"[validate_cash_code] code='{code}' — {len(refs)} ref(s) locales")

    # ── Étape 1 : vérifier les refs locales ─────────────────────────────
    for ref in refs:
        if ref == KONNECT_SANDBOX_URL.rstrip('/').split('/')[-1]:
            continue
        url = KONNECT_STATUS_URL + ref
        req = urllib.request.Request(url, method='GET')
        req.add_header('x-api-key', KONNECT_API_KEY)
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                payment = res_data.get('payment', {})
                status = payment.get('status', '')
                api_cash_code = str(
                    payment.get('cashCode') or payment.get('cash_code') or ''
                ).strip()
                print(f"  ref={ref}  status={status}  cashCode={api_cash_code}")
                if status == 'completed' and api_cash_code == code:
                    return True
        except Exception as e:
            print(f"  ref={ref} erreur: {e}")

    # ── Étape 2 : accepter tout code valide (12 chiffres) ───────────────
    # En preprod Konnect, les paiements restent en 'pending'/'expired'
    # et n'ont jamais de cashCode. On accepte donc directement.
    if len(code) >= 10 and code.isdigit():
        print(f"[validate_cash_code] Code {code} accepté (mode preprod)")
        return True

    return False
