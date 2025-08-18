#!/usr/bin/env python3
"""
Test script for Imagyn MCP Server
"""

import asyncio
import json
import os
from pathlib import Path

# Add src to path
import sys
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from imagyn.models import ImagynConfig
from imagyn.comfyui_client import ComfyUIClient
from imagyn.storage import ImageStorage


async def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    try:
        config = ImagynConfig.load_from_file("config.json")
        print(f"✅ Config loaded successfully")
        print(f"   ComfyUI URL: {config.comfyui_url}")
        print(f"   Workflow: {config.workflow_file}")
        print(f"   LoRAs enabled: {config.enable_loras}")
        return config
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return None


async def test_workflow():
    """Test workflow file loading"""
    print("\n📋 Testing workflow file...")
    try:
        config = ImagynConfig.load_from_file("config.json")
        workflow_path = Path(config.workflow_file)
        
        if not workflow_path.exists():
            print(f"❌ Workflow file not found: {config.workflow_file}")
            return None
        
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        print(f"✅ Workflow loaded successfully")
        print(f"   Nodes: {len(workflow)}")
        print(f"   File: {config.workflow_file}")
        return workflow
    except Exception as e:
        print(f"❌ Workflow loading failed: {e}")
        return None


async def test_comfyui_connection():
    """Test ComfyUI server connection"""
    print("\n🔌 Testing ComfyUI connection...")
    try:
        config = ImagynConfig.load_from_file("config.json")
        
        async with ComfyUIClient(config.comfyui_url) as client:
            connected = await client.check_connection()
            
            if connected:
                print(f"✅ ComfyUI server is reachable")
                print(f"   URL: {config.comfyui_url}")
            else:
                print(f"❌ ComfyUI server is not reachable")
                print(f"   URL: {config.comfyui_url}")
                print(f"   Make sure ComfyUI is running and accessible")
            
            return connected
    except Exception as e:
        print(f"❌ ComfyUI connection test failed: {e}")
        return False


async def test_storage():
    """Test storage system"""
    print("\n💾 Testing storage system...")
    try:
        config = ImagynConfig.load_from_file("config.json")
        storage = ImageStorage(config.output_folder)
        
        stats = await storage.get_storage_stats()
        print(f"✅ Storage system initialized")
        print(f"   Output folder: {stats['output_folder']}")
        print(f"   Existing images: {stats['total_images']}")
        print(f"   Total size: {stats['total_size_mb']} MB")
        
        return True
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False


async def test_loras():
    """Test LoRA discovery"""
    print("\n🎨 Testing LoRA discovery...")
    try:
        config = ImagynConfig.load_from_file("config.json")
        
        if not config.enable_loras:
            print("ℹ️  LoRAs are disabled in configuration")
            return True
        
        async with ComfyUIClient(config.comfyui_url) as client:
            loras = await client.get_available_loras(config.lora_folder_path)
            
            print(f"✅ LoRA discovery completed")
            print(f"   Folder: {config.lora_folder_path}")
            print(f"   Found: {len(loras)} LoRA models")
            
            for lora in loras[:5]:  # Show first 5
                print(f"   - {lora.name}")
            
            if len(loras) > 5:
                print(f"   ... and {len(loras) - 5} more")
            
            return True
    except Exception as e:
        print(f"❌ LoRA discovery failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Imagyn MCP Server Test Suite")
    print("=" * 40)
    
    tests = [
        test_config,
        test_workflow,
        test_storage,
        test_loras,
        test_comfyui_connection,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result is not None and result is not False)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Imagyn MCP Server is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and setup.")
        print("\nCommon fixes:")
        print("- Ensure ComfyUI server is running")
        print("- Check config.json paths are correct")
        print("- Verify workflow files exist")
        print("- Check LoRA folder permissions")


if __name__ == "__main__":
    asyncio.run(main())
