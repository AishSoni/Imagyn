#!/usr/bin/env python3
"""
Test script for workflow-agnostic image generation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.comfyui_client import ComfyUIClient
from imagyn.models import ImagynConfig

async def test_workflow_analysis():
    """Test the workflow analysis functionality"""
    
    # Load config and workflow
    config = ImagynConfig.load_from_file("config.json")
    
    with open(config.workflow_file, 'r') as f:
        workflow = json.load(f)
    
    print("=== Workflow Analysis ===")
    
    async with ComfyUIClient(config.comfyui_url) as client:
        # Test node finding
        clip_nodes = client._find_nodes_by_class_type(workflow, "CLIPTextEncode")
        print(f"Found CLIPTextEncode nodes: {clip_nodes}")
        
        sampler_nodes = client._find_nodes_by_class_type(workflow, "KSampler")
        print(f"Found KSampler nodes: {sampler_nodes}")
        
        latent_nodes = client._find_nodes_by_class_type(workflow, "EmptySD3LatentImage")
        print(f"Found EmptySD3LatentImage nodes: {latent_nodes}")
        
        lora_nodes = client._find_nodes_by_class_type(workflow, "LoraLoader")
        print(f"Found LoraLoader nodes: {lora_nodes}")
        
        # Test available LoRAs
        if config.enable_loras:
            available_loras = await client.get_available_loras(config.lora_folder_path)
            print(f"Available LoRAs: {[lora.name for lora in available_loras[:5]]}")  # Show first 5
        
        print("\n=== Testing Workflow Modification ===")
        
        # Test workflow modification
        test_workflow = json.loads(json.dumps(workflow))
        
        # Apply test prompt
        pos_node, neg_node = client._apply_prompt_to_workflow(
            test_workflow, 
            "a beautiful sunset over mountains", 
            "blurry, ugly"
        )
        print(f"Applied prompts to nodes - Positive: {pos_node}, Negative: {neg_node}")
        
        # Apply test seed
        client._apply_seed_to_workflow(test_workflow, 12345)
        print("Applied seed: 12345")
        
        # Apply test dimensions
        client._apply_dimensions_to_workflow(test_workflow, 512, 768)
        print("Applied dimensions: 512x768")
        
        # Apply test LoRA
        if config.enable_loras and available_loras:
            client._apply_loras_to_workflow(
                test_workflow, 
                [available_loras[0].name], 
                True, 
                config.lora_folder_path
            )
            print(f"Applied LoRA: {available_loras[0].name}")
        
        print("\n=== Workflow Modification Successful ===")
        print("The workflow-agnostic system is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_workflow_analysis())
