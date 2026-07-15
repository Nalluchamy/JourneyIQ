import httpx

async def main():
    base_url = "https://journeyiq-yq7k.onrender.com"
    email = "admin@journeyiq.in"
    password = "Admin@1234"
    product_id = 733
    session_id = "d3b07384-d113-4956-a50e-72d8e3d03704"

    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        login_data = {"username": email, "password": password}
        resp = await client.post(
            f"{base_url}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "x-session-id": session_id}
        
        # 2. Get Product Detail
        print("\nQuerying Product detail...")
        resp = await client.get(f"{base_url}/api/v1/products/{product_id}", headers=headers)
        print(f"Product detail status: {resp.status_code} - {resp.text[:100]}")
        
        # 3. Get Reviews
        print("\nQuerying Reviews...")
        resp = await client.get(f"{base_url}/api/v1/products/{product_id}/reviews", headers=headers)
        print(f"Reviews status: {resp.status_code} - {resp.text[:100]}")
        
        # 4. Get Similar
        print("\nQuerying Similar...")
        resp = await client.get(f"{base_url}/api/v1/products/{product_id}/similar", headers=headers)
        print(f"Similar status: {resp.status_code} - {resp.text[:100]}")
        
        # 5. Get Recent Views
        print("\nQuerying Recent Views...")
        resp = await client.get(f"{base_url}/api/v1/events/recent-views?session_id={session_id}", headers=headers)
        print(f"Recent Views status: {resp.status_code} - {resp.text[:100]}")
        
        # 6. Get Wishlist
        print("\nQuerying Wishlist...")
        resp = await client.get(f"{base_url}/api/v1/wishlist", headers=headers)
        print(f"Wishlist status: {resp.status_code} - {resp.text[:100]}")
        
        # 7. Get Cart
        print("\nQuerying Cart...")
        resp = await client.get(f"{base_url}/api/v1/cart", headers=headers)
        print(f"Cart status: {resp.status_code} - {resp.text[:100]}")

import asyncio
asyncio.run(main())
