import asyncio
import time
import httpx

BASE_URL = "http://localhost:8000/api/v1"
CONCURRENT_USERS = 100
REQUESTS_PER_USER = 5
TARGETS = [
    "/system/live",
    "/system/ready",
    "/system/health",
]

async def simulate_user(client: httpx.AsyncClient, user_id: int) -> list[float]:
    latencies = []
    for _ in range(REQUESTS_PER_USER):
        for path in TARGETS:
            start = time.perf_counter()
            try:
                res = await client.get(f"{BASE_URL}{path}")
                elapsed = time.perf_counter() - start
                latencies.append(elapsed)
            except Exception:
                pass
            await asyncio.sleep(0.01) # short pause
    return latencies

async def main():
    print(f"Starting load test simulation...")
    print(f"Concurrent Users: {CONCURRENT_USERS}")
    print(f"Requests per User: {REQUESTS_PER_USER}")
    print(f"Targets: {TARGETS}")

    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        tasks = [simulate_user(client, i) for i in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

    flat_latencies = [l for user_lat in results for l in user_lat]
    if flat_latencies:
        avg_latency = sum(flat_latencies) / len(flat_latencies)
        min_latency = min(flat_latencies)
        max_latency = max(flat_latencies)
        print("\n=== LOAD TEST RESULTS ===")
        print(f"Total Requests: {len(flat_latencies)}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Latency: {avg_latency*1000:.2f} ms")
        print(f"Min Latency: {min_latency*1000:.2f} ms")
        print(f"Max Latency: {max_latency*1000:.2f} ms")
        print(f"Requests/sec: {len(flat_latencies) / total_time:.2f}")
    else:
        print("No successful requests recorded. Ensure the dev server is running on http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(main())
