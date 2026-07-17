import os
import asyncio
from google import genai
from google.genai import types

import pytest

@pytest.mark.asyncio
async def test_genai():
    # Use mock key or public if required, but here we just want to see if the interface is correct
    client = genai.Client(api_key="dummy")
    try:
        print("Checking if client.models.generate_content exists...")
        print(client.models.generate_content)
        
        print("Checking types.GenerateContentConfig...")
        config = types.GenerateContentConfig(system_instruction="You are a helpful assistant")
        print(config)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_genai())
