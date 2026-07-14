import argparse
import sys
import httpx

def main():
    parser = argparse.ArgumentParser(description="JourneyIQ v1.5 Smoke Tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API backend target url")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"Starting smoke tests against target: {base_url}")
    
    # 1. Verify Health endpoints
    endpoints = [
        "/api/v1/health",
        "/api/v1/live",
        "/api/v1/ready",
        "/api/v1/system/version"
    ]
    
    for ep in endpoints:
        url = base_url + ep
        try:
            resp = httpx.get(url, timeout=10.0)
            print(f"GET {ep} -> Status {resp.status_code}")
            if resp.status_code != 200:
                print(f"Error: {ep} returned non-200 code")
                sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to connect to {url}: {e}")
            sys.exit(1)

    # 2. Verify Auth (Login endpoint exists)
    try:
        url = base_url + "/api/v1/auth/login"
        # Mock request with empty/dummy payload
        resp = httpx.post(url, data={"username": "user", "password": "pwd"}, timeout=10.0)
        # Auth login should return 400 or 401 on bad credentials, but the endpoint must exist (i.e. not 404)
        print(f"POST /api/v1/auth/login -> Status {resp.status_code}")
        if resp.status_code == 404:
            print("Error: Auth login endpoint not found")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking login endpoint: {e}")
        sys.exit(1)

    # 3. Verify recommendations config exists
    try:
        url = base_url + "/api/v1/recommendations/trending"
        resp = httpx.get(url, timeout=10.0)
        print(f"GET /api/v1/recommendations/trending -> Status {resp.status_code}")
        if resp.status_code not in (200, 401, 307): # 401 is fine if auth required
            print(f"Error: Trending recommendations endpoint returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking recommendations endpoint: {e}")
        sys.exit(1)

    # 4. Verify agent endpoints exist
    try:
        url = base_url + "/api/v1/agent/status"
        resp = httpx.get(url, timeout=10.0)
        print(f"GET /api/v1/agent/status -> Status {resp.status_code}")
        if resp.status_code not in (200, 401):
            print(f"Error: Agent status returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking agent status endpoint: {e}")
        sys.exit(1)

    # 5. Verify copilot summary exists
    try:
        url = base_url + "/api/v1/copilot/summary"
        resp = httpx.get(url, timeout=10.0)
        print(f"GET /api/v1/copilot/summary -> Status {resp.status_code}")
        if resp.status_code not in (200, 401):
            print(f"Error: Copilot summary returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking copilot summary endpoint: {e}")
        sys.exit(1)

    # 6. Verify assistant endpoints exist
    try:
        url = base_url + "/api/v1/assistant/suggestions"
        resp = httpx.get(url, timeout=10.0)
        print(f"GET /api/v1/assistant/suggestions -> Status {resp.status_code}")
        if resp.status_code not in (200, 401):
            print(f"Error: Assistant autocomplete suggestions returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking assistant suggestions: {e}")
        sys.exit(1)

    print("Smoke tests passed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()
