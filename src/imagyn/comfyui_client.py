"""
ComfyUI API client for image generation
"""

import asyncio
import json
import uuid
import websockets
import httpx
import base64
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import time

from .models import ComfyUIWorkflowRequest, GenerationMetadata, LoRAInfo


class ComfyUIClient:
    """Client for interacting with ComfyUI API"""
    
    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url.rstrip('/')
        self.ws_url = self.base_url.replace('http', 'ws')
        self.client_id = str(uuid.uuid4())
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
    
    async def check_connection(self) -> bool:
        """Check if ComfyUI server is accessible"""
        try:
            response = await self.http_client.get(f"{self.base_url}/system_stats")
            return response.status_code == 200
        except Exception:
            return False
    
    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a workflow for execution and return prompt ID"""
        request = ComfyUIWorkflowRequest(
            client_id=self.client_id,
            prompt=workflow
        )
        
        response = await self.http_client.post(
            f"{self.base_url}/prompt",
            json=request.to_dict()
        )
        response.raise_for_status()
        
        result = response.json()
        return result["prompt_id"]
    
    async def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for workflow completion via WebSocket"""
        ws_url = f"{self.ws_url}/ws?clientId={self.client_id}"
        
        start_time = time.time()
        
        async with websockets.connect(ws_url) as websocket:
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data["type"] == "executing":
                        executing_data = data["data"]
                        if executing_data["node"] is None and executing_data["prompt_id"] == prompt_id:
                            # Execution completed
                            return await self.get_history(prompt_id)
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
        
        raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        response = await self.http_client.get(f"{self.base_url}/history/{prompt_id}")
        response.raise_for_status()
        
        history = response.json()
        return history.get(prompt_id, {})
    
    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download image from ComfyUI"""
        params = {
            "filename": filename,
            "type": folder_type
        }
        if subfolder:
            params["subfolder"] = subfolder
        
        response = await self.http_client.get(
            f"{self.base_url}/view",
            params=params
        )
        response.raise_for_status()
        
        return response.content
    
    async def generate_image(
        self,
        workflow_template: Dict[str, Any],
        prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        loras: Optional[List[str]] = None,
        width: int = 1024,
        height: int = 1024
    ) -> Tuple[bytes, GenerationMetadata]:
        """Generate an image using the provided workflow template"""
        
        # Create a copy of the workflow template
        workflow = json.loads(json.dumps(workflow_template))
        
        # Set the prompt
        if "2" in workflow:  # Positive prompt node
            workflow["2"]["inputs"]["text"] = prompt
        
        # Set negative prompt
        if "5" in workflow:  # Negative prompt node
            workflow["5"]["inputs"]["text"] = negative_prompt
        
        # Set seed
        if seed is None:
            seed = int(time.time()) % (2**32)
        if "3" in workflow:  # KSampler node
            workflow["3"]["inputs"]["seed"] = seed
        
        # Set dimensions
        if "4" in workflow:  # Empty latent image node
            workflow["4"]["inputs"]["width"] = width
            workflow["4"]["inputs"]["height"] = height
        
        # Apply LoRAs if provided and LoRA loader node exists
        if loras and "8" in workflow:  # LoRA loader node
            if len(loras) > 0:
                # For now, use the first LoRA (in a full implementation, 
                # you'd chain multiple LoRA loaders)
                lora_name = f"{loras[0]}.safetensors"
                workflow["8"]["inputs"]["lora_name"] = lora_name
                workflow["8"]["inputs"]["strength_model"] = 1.0
                workflow["8"]["inputs"]["strength_clip"] = 1.0
            else:
                workflow["8"]["inputs"]["lora_name"] = "None"
        
        start_time = time.time()
        
        # Queue the workflow
        prompt_id = await self.queue_prompt(workflow)
        
        # Wait for completion
        history = await self.wait_for_completion(prompt_id)
        
        generation_time = time.time() - start_time
        
        # Extract output information
        outputs = history.get("outputs", {})
        save_image_outputs = None
        
        # Find the SaveImage node output (usually node "7")
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                save_image_outputs = node_output["images"]
                break
        
        if not save_image_outputs:
            raise RuntimeError("No image output found in workflow execution")
        
        # Get the first image
        image_info = save_image_outputs[0]
        image_data = await self.get_image(
            image_info["filename"],
            image_info.get("subfolder", ""),
            image_info.get("type", "output")
        )
        
        # Create metadata
        metadata = GenerationMetadata(
            prompt=prompt,
            negative_prompt=negative_prompt,
            loras_used=loras or [],
            generation_time=generation_time,
            seed=seed,
            width=width,
            height=height,
            workflow_used="txt2img_flux"
        )
        
        return image_data, metadata
    
    async def get_available_loras(self, lora_folder: str) -> List[LoRAInfo]:
        """Get list of available LoRA models"""
        loras = []
        
        if not os.path.exists(lora_folder):
            return loras
        
        lora_path = Path(lora_folder)
        for lora_file in lora_path.glob("*.safetensors"):
            lora_info = LoRAInfo(
                name=lora_file.stem,
                file_path=str(lora_file),
                description=f"LoRA model: {lora_file.stem}",
                tags=["lora", "style"]
            )
            loras.append(lora_info)
        
        return loras
