"""
Test script to validate the Replicate integration
"""
import asyncio
import os
from src.imagyn.models import ImagynConfig, ReplicateConfig
from src.imagyn.replicate_client import ReplicateClient


async def test_replicate_config():
    """Test Replicate configuration loading"""
    print("Testing Replicate configuration...")
    
    # Test config loading
    config = ImagynConfig.load_from_file('config.replicate.example.json')
    print(f"✅ Config loaded: provider={config.provider}")
    print(f"✅ Model ID: {config.replicate.model_id}")
    print(f"✅ Speed mode: {config.replicate.default_speed_mode}")
    

async def test_replicate_client():
    """Test Replicate client (requires API key)"""
    print("\nTesting Replicate client...")
    
    # This requires a real API key to work
    api_key = os.getenv('REPLICATE_API_TOKEN')
    if not api_key:
        print("⚠️  No REPLICATE_API_TOKEN environment variable found")
        print("   Set your API key to test actual connection:")
        print("   export REPLICATE_API_TOKEN=your_api_key_here")
        return
    
    model_id = "prunaai/flux.1-dev:b0306d92aa025bb747dc74162f3c27d6ed83798e08e5f8977adf3d859d0536a3"
    
    async with ReplicateClient(api_key, model_id) as client:
        # Test connection
        connected = await client.check_connection()
        if connected:
            print("✅ Successfully connected to Replicate API")
            
            # Get model info
            model_info = await client.get_model_info()
            print(f"✅ Model: {model_info.get('name', 'Unknown')}")
            print(f"✅ Owner: {model_info.get('owner', 'Unknown')}")
        else:
            print("❌ Failed to connect to Replicate API")


async def main():
    print("Imagyn Replicate Integration Test")
    print("=" * 40)
    
    await test_replicate_config()
    await test_replicate_client()
    
    print("\n" + "=" * 40)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
