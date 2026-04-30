import urllib.request
import json

refs = json.load(open("payment_refs.json"))
api_key = "68036ba4c4f4ab1d9ffb00e7:TZYBj46FXgRwyF9A8x5Df2vIenLMaBZ"

print(f"=== {len(refs)} refs trouvees ===\n")

for ref in refs:
    url = f"https://api.preprod.konnect.network/api/v2/payments/{ref}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("x-api-key", api_key)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        payment = data.get("payment", {})
        status = payment.get("status")
        cash_code = payment.get("cashCode") or payment.get("cash_code")
        amount = payment.get("amount")
        print(f"ref={ref}")
        print(f"  status   = {status}")
        print(f"  cashCode = {cash_code}")
        print(f"  amount   = {amount}")
        print()
    except Exception as e:
        print(f"ref={ref}  ERREUR: {e}\n")
