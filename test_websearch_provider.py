import asyncio
import os
from faos.services.provider.websearch_impl import WebSearchProvider
from faos.services.provider.models import ProviderRequest

async def main():
    provider = WebSearchProvider()
    print("Testing WebSearchProvider (Attempt 1 - Fetching)...")
    req = ProviderRequest(entity="全球财经新闻 宏观经济 (site:cls.cn OR site:wallstreetcn.com)")
    
    resp1 = await provider.fetch(req)
    print("\nAttempt 1 Status:", resp1.status)
    
    print("\nTesting WebSearchProvider (Attempt 2 - Should Hit Cache)...")
    resp2 = await provider.fetch(req)
    print("\nAttempt 2 Status:", resp2.status)
    
    if resp2.status == "success":
        print("\nResults from Cache:")
        for i, item in enumerate(resp2.data):
            print(f"[{i+1}] {item.get('title')} ({item.get('source')})")

if __name__ == "__main__":
    asyncio.run(main())
