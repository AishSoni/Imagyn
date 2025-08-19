"""
Replicate API client for image generation
"""

import asyncio
import httpx
import json
import time
import uuid
from typing import Dict, Optional, Tuple, Any
from .models import GenerationMetadata


class ReplicateClient:
    """Client for interacting with Replicate API"""
    
    def __init__(self, api_key: str, model_id: str, default_speed_mode: str = "Extra Juiced 🔥 (more speed)"):
        self.api_key = api_key
        self.model_id = model_id
        self.default_speed_mode = default_speed_mode
        self.base_url = "https://api.replicate.com/v1"
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": f"Token {api_key}"},
            timeout=300.0  # Extended timeout for image generation
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
    
    async def check_connection(self) -> bool:
        """Check if Replicate API is accessible with the provided API key"""
        try:
            response = await self.http_client.get(f"{self.base_url}/account")
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
        speed_mode: Optional[str] = None,
        **kwargs
    ) -> Tuple[bytes, GenerationMetadata]:
        """Generate an image using Replicate API"""
        
        start_time = time.time()
        
        # Prepare input for Replicate
        input_data = {
            "prompt": prompt,
            "speed_mode": speed_mode or self.default_speed_mode,
            "width": width,
            "height": height,
        }
        
        # Add negative prompt if provided
        if negative_prompt:
            # Some models might not support negative prompts directly
            # We'll add it to the prompt as a guidance
            input_data["prompt"] = f"{prompt}. Avoid: {negative_prompt}"
        
        # Add seed if provided
        if seed is not None:
            input_data["seed"] = seed
        
        # Create prediction
        prediction_response = await self.http_client.post(
            f"{self.base_url}/predictions",
            json={
                "version": self.model_id.split(":")[-1],  # Extract version from model_id
                "input": input_data
            }
        )
        prediction_response.raise_for_status()
        
        prediction = prediction_response.json()
        prediction_id = prediction["id"]
        
        # Wait for completion
        while True:
            status_response = await self.http_client.get(
                f"{self.base_url}/predictions/{prediction_id}"
            )
            status_response.raise_for_status()
            
            status_data = status_response.json()
            status = status_data["status"]
            
            if status == "succeeded":
                # Get the output URL
                output_url = status_data["output"]
                if isinstance(output_url, list) and output_url:
                    output_url = output_url[0]
                
                # Download the image
                image_response = await httpx.AsyncClient().get(output_url)
                image_response.raise_for_status()
                image_data = image_response.content
                
                # Generate a seed if none was provided
                actual_seed = seed if seed is not None else hash(prompt + str(time.time())) % (2**31)
                
                # Create metadata
                generation_time = time.time() - start_time
                metadata = GenerationMetadata(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    loras_used=[],  # Replicate doesn't use LoRAs in the same way
                    generation_time=generation_time,
                    seed=actual_seed,
                    width=width,
                    height=height,
                    steps=0,  # Replicate doesn't expose step count
                    cfg=0.0,  # Replicate doesn't expose CFG
                    workflow_used=f"replicate:{self.model_id}"
                )
                
                return image_data, metadata
                
            elif status == "failed":
                error_message = status_data.get("error", "Unknown error occurred")
                raise Exception(f"Replicate generation failed: {error_message}")
            
            elif status in ["starting", "processing"]:
                # Wait before checking again
                await asyncio.sleep(2)
            else:
                raise Exception(f"Unexpected status: {status}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model"""
        try:
            # Extract owner and name from model_id (format: owner/name:version)
            model_parts = self.model_id.split(":")
            if len(model_parts) != 2:
                raise ValueError(f"Invalid model_id format: {self.model_id}")
            
            owner_name = model_parts[0]
            version = model_parts[1]
            
            response = await self.http_client.get(f"{self.base_url}/models/{owner_name}")
            response.raise_for_status()
            
            model_data = response.json()
            return {
                "name": model_data.get("name", "Unknown"),
                "description": model_data.get("description", ""),
                "version": version,
                "owner": model_data.get("owner", "Unknown")
            }
        except Exception as e:
            return {
                "name": "Unknown Model",
                "description": f"Error retrieving model info: {str(e)}",
                "version": "Unknown",
                "owner": "Unknown"
            }
