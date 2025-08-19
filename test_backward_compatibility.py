#!/usr/bin/env python3
"""
Test script to validate backward compatibility with old config files
"""

import json
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.models import ImagynConfig


def test_backward_compatibility():
    """Test that old config files with lora_folder_path still work"""
    
    print("Testing Backward Compatibility...")
    
    # Create an old-style config with lora_folder_path
    old_config = {
        "comfyui_url": "http://localhost:8000",
        "workflow_file": "workflows/fluxkrea.json",
        "enable_loras": True,
        "lora_folder_path": "/old/path/to/loras/",  # This should be ignored
        "output_folder": "output",
        "max_concurrent_generations": 3,
        "default_generation_timeout": 300,
        "http_timeout": 60.0,
        "websocket_timeout": 30.0
    }
    
    # Save temporary old config
    old_config_path = "test_old_config.json"
    with open(old_config_path, 'w') as f:
        json.dump(old_config, f, indent=2)
    
    try:
        # Test loading old config
        print("\n1. Testing old config file loading...")
        config = ImagynConfig.load_from_file(old_config_path)
        
        print("✅ Old config loaded successfully")
        print(f"   ComfyUI URL: {config.comfyui_url}")
        print(f"   LoRAs enabled: {config.enable_loras}")
        
        # Verify lora_folder_path is not in the loaded config
        if not hasattr(config, 'lora_folder_path'):
            print("✅ lora_folder_path correctly removed from config")
        else:
            print("❌ lora_folder_path still present in config")
            
        # Test new config file loading
        print("\n2. Testing new config file loading...")
        new_config = ImagynConfig.load_from_file('config.json')
        
        print("✅ New config loaded successfully")
        print(f"   ComfyUI URL: {new_config.comfyui_url}")
        print(f"   LoRAs enabled: {new_config.enable_loras}")
        
        if not hasattr(new_config, 'lora_folder_path'):
            print("✅ New config has no lora_folder_path field")
        else:
            print("❌ New config unexpectedly has lora_folder_path field")
            
        print("\n✅ All backward compatibility tests passed!")
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test config
        if Path(old_config_path).exists():
            Path(old_config_path).unlink()


if __name__ == "__main__":
    test_backward_compatibility()
