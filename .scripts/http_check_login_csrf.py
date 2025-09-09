import requests

resp = requests.get("http://127.0.0.1:8000/accounts/login/")
print("status:", resp.status_code)
print("set-cookie headers:")
for k, v in resp.headers.items():
    if k.lower().startswith("set-cookie"):
        print(k + ":", v)
print(
    "\nHas sessionid cookie in response headers:",
    "sessionid" in resp.headers.get("set-cookie", ""),
)
print("\nBody snippet:\n", resp.text[:1200])
