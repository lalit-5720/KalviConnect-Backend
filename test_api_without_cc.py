import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/api/auth/send-otp/'
data = json.dumps({'phone': '6383205635'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print("Status Code:", response.getcode())
    print("Response:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Status Code:", e.code)
    print("Response:", e.read().decode('utf-8'))
