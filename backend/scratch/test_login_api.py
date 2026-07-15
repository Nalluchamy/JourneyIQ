import httpx
import time

url = "https://journeyiq-yq7k.onrender.com/api/v1/auth/login"
data = {
    "username": "admin@journeyiq.in",
    "password": "Admin@1234"
}

print(f"Sending POST to {url}...")
start = time.time()
try:
    resp = httpx.post(url, data=data, timeout=15.0)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
print(f"Time taken: {time.time() - start:.2f} seconds")
