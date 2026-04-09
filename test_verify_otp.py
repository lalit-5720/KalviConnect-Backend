import json
import urllib.request
import urllib.error

base_url = 'http://127.0.0.1:8000/api/auth/'

# 1. Provide the exact OTP here:
OTP_TO_TEST = '123456' # <-- Put your OTP here and run!

req_verify = urllib.request.Request(
    base_url + 'verify-otp/',
    data=json.dumps({
        'phone': '+919876543210', 
        'otp': OTP_TO_TEST,
        'role': 'teacher'  # <-- THIS IS REQUIRED!
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    response = urllib.request.urlopen(req_verify)
    print("Verify OTP Status Code:", response.getcode())
    print("Verify OTP Response:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Verify OTP Status Code:", e.code)
    print("Verify OTP Response:", e.read().decode('utf-8'))
