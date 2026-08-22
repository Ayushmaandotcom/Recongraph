import asyncio
import aiohttp
import time
import argparse

async def fetch(session, url, payload):
    start = time.time()
    try:
        async with session.post(url, json=payload) as response:
            status = response.status
            data = await response.json()
            latency = time.time() - start
            return status, latency, data
    except Exception as e:
        latency = time.time() - start
        return 500, latency, str(e)

async def load_test(url, num_requests, concurrency, payload):
    print(f"Starting load test with {num_requests} requests, concurrency {concurrency}")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_fetch():
            async with semaphore:
                return await fetch(session, url, payload)
                
        for _ in range(num_requests):
            tasks.append(asyncio.create_task(bounded_fetch()))
            
        results = await asyncio.gather(*tasks)
        
    latencies = [r[1] for r in results]
    statuses = [r[0] for r in results]
    
    successes = statuses.count(200)
    failures = len(statuses) - successes
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    print("\n--- Load Test Results ---")
    print(f"Total Requests: {num_requests}")
    print(f"Successes:      {successes}")
    print(f"Failures:       {failures}")
    print(f"Avg Latency:    {avg_latency:.3f}s")
    print(f"Max Latency:    {max_latency:.3f}s")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/copilot/ask")
    parser.add_argument("-n", "--num-requests", type=int, default=50)
    parser.add_argument("-c", "--concurrency", type=int, default=10)
    args = parser.parse_args()
    
    payload = {
        "tenant_id": "test_tenant",
        "user_id": "test_user",
        "query": "What is the time limit for claiming ITC?"
    }
    
    asyncio.run(load_test(args.url, args.num_requests, args.concurrency, payload))
