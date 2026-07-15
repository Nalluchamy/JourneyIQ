import asyncio
import asyncpg

async def try_conn(url):
    print(f"Testing URL: {url}")
    try:
        conn = await asyncpg.connect(url, timeout=5.0)
        print("✓ SUCCESS!")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__} - {e}")
        return False

async def main():
    p1 = "bWDsNo41jfgMIBke"
    p2 = "hWDsNo41jfgMTBkc"
    p3 = "Bqk6qtno8GRiMyMp"
    
    hosts = [
        "aws-1-ap-south-1.pooler.supabase.com:6543",
        "aws-1-ap-south-1.pooler.supabase.com:5432"
    ]
    
    for host in hosts:
        for p in [p1, p2, p3]:
            user = "postgres.qhkbuszwzxejyataswph"
            url = f"postgresql://{user}:{p}@{host}/postgres"
            await try_conn(url)

asyncio.run(main())
