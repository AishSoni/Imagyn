"""
ComfyUI API client for image generation
"""

import asyncio
import json
import uuid
import websockets
import httpx
import base64
from typing import Dict, List, Optional, Any, Tuple
import time

from .models import ComfyUIWorkflowRequest, GenerationMetadata, LoRAInfo


class ComfyUIClient:
    """Client for interacting with ComfyUI API"""
    
    def __init__(self, base_url: str = "http://localhost:8188", http_timeout: float = 60.0, websocket_timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.ws_url = self.base_url.replace('http', 'ws')
        self.client_id = str(uuid.uuid4())
        self.http_timeout = http_timeout
        self.websocket_timeout = websocket_timeout
        self.http_client = httpx.AsyncClient(timeout=self.http_timeout)
    
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
                    message = await asyncio.wait_for(websocket.recv(), timeout=self.websocket_timeout)
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
    
    def _find_nodes_by_class_type(self, workflow: Dict[str, Any], class_type: str) -> List[str]:
        """Find all nodes of a specific class type in the workflow"""
        matching_nodes = []
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == class_type:
                matching_nodes.append(node_id)
        return matching_nodes
    
    def _find_node_by_class_type(self, workflow: Dict[str, Any], class_type: str) -> Optional[str]:
        """Find the first node of a specific class type in the workflow"""
        nodes = self._find_nodes_by_class_type(workflow, class_type)
        return nodes[0] if nodes else None
    
    def _apply_prompt_to_workflow(self, workflow: Dict[str, Any], prompt: str, negative_prompt: str = ""):
        """Apply positive and negative prompts to appropriate nodes in the workflow"""
        # Find CLIP Text Encode nodes for prompts
        clip_text_nodes = self._find_nodes_by_class_type(workflow, "CLIPTextEncode")
        
        # Strategy: Look for nodes with text inputs and try to determine which is positive/negative
        positive_node = None
        negative_node = None
        
        for node_id in clip_text_nodes:
            node = workflow[node_id]
            current_text = node.get("inputs", {}).get("text", "").lower()
            
            # Heuristics to determine if this is a negative prompt node
            if any(neg_word in current_text for neg_word in ["negative", "bad", "worst", "ugly", "blurry"]):
                if negative_node is None:
                    negative_node = node_id
            else:
                if positive_node is None:
                    positive_node = node_id
        
        # If we couldn't determine by content, use order (first is usually positive)
        if positive_node is None and clip_text_nodes:
            positive_node = clip_text_nodes[0]
        if negative_node is None and len(clip_text_nodes) > 1:
            negative_node = clip_text_nodes[1]
        
        # Apply prompts
        if positive_node:
            workflow[positive_node]["inputs"]["text"] = prompt
        if negative_node and negative_prompt:
            workflow[negative_node]["inputs"]["text"] = negative_prompt
        elif negative_prompt and positive_node:
            # If no dedicated negative node, append to positive prompt
            combined_prompt = f"{prompt}. Avoid: {negative_prompt}"
            workflow[positive_node]["inputs"]["text"] = combined_prompt
            
        return positive_node, negative_node
    
    def _apply_seed_to_workflow(self, workflow: Dict[str, Any], seed: int):
        """Apply seed to sampling nodes in the workflow"""
        # Find sampling nodes that accept seeds
        sampling_classes = ["KSampler", "KSamplerAdvanced", "SamplerCustom"]
        
        for class_type in sampling_classes:
            nodes = self._find_nodes_by_class_type(workflow, class_type)
            for node_id in nodes:
                if "seed" in workflow[node_id].get("inputs", {}):
                    workflow[node_id]["inputs"]["seed"] = seed
    
    def _apply_dimensions_to_workflow(self, workflow: Dict[str, Any], width: int, height: int):
        """Apply dimensions to empty latent image nodes in the workflow"""
        # Find Empty Latent Image nodes (various types)
        latent_classes = ["EmptyLatentImage", "EmptySD3LatentImage", "EmptyFluxLatentImage"]
        
        for class_type in latent_classes:
            nodes = self._find_nodes_by_class_type(workflow, class_type)
            for node_id in nodes:
                node = workflow[node_id]
                if "width" in node.get("inputs", {}):
                    node["inputs"]["width"] = width
                if "height" in node.get("inputs", {}):
                    node["inputs"]["height"] = height
    
    async def _apply_loras_to_workflow(self, workflow: Dict[str, Any], loras: List[str], enable_loras: bool):
        """Apply LoRAs to LoRA loader nodes in the workflow"""
        if not enable_loras or not loras:
            return
            
        # Find LoRA loader nodes
        lora_nodes = self._find_nodes_by_class_type(workflow, "LoraLoader")
        
        # Apply first LoRA to first LoRA node (can be extended for multiple LoRAs)
        if lora_nodes and loras:
            lora_node_id = lora_nodes[0]
            lora_node = workflow[lora_node_id]
            
            # Get available LoRAs from server to validate
            available_loras = await self._get_available_loras_from_server()
            available_lora_names = [lora.file_path for lora in available_loras]
            
            # Find the best match for the requested LoRA
            lora_name = loras[0]
            
            # Try exact match first
            if lora_name in available_lora_names:
                selected_lora = lora_name
            elif f"{lora_name}.safetensors" in available_lora_names:
                selected_lora = f"{lora_name}.safetensors"
            else:
                # Try to find a partial match
                selected_lora = None
                for available_lora in available_lora_names:
                    if lora_name.lower() in available_lora.lower():
                        selected_lora = available_lora
                        break
                
                # If no match found, use the first available LoRA as fallback
                if not selected_lora and available_lora_names:
                    selected_lora = available_lora_names[0]
                elif not selected_lora:
                    # No LoRAs available at all, skip application
                    return
            
            lora_node["inputs"]["lora_name"] = selected_lora
            
            # Set default strengths if they exist
            if "strength_model" in lora_node["inputs"]:
                lora_node["inputs"]["strength_model"] = 1.0
            if "strength_clip" in lora_node["inputs"]:
                lora_node["inputs"]["strength_clip"] = 1.0
    
    async def _get_available_loras_from_server(self) -> List:
        """Get list of available LoRA models from ComfyUI server"""
        from .models import LoRAInfo
        
        try:
            # Query the object_info endpoint to get available models
            response = await self.http_client.get(f"{self.base_url}/object_info")
            response.raise_for_status()
            
            object_info = response.json()
            loras = []
            
            # Look for LoraLoader node information
            lora_loader_info = object_info.get("LoraLoader", {})
            input_info = lora_loader_info.get("input", {})
            required_inputs = input_info.get("required", {})
            
            # Get LoRA names from the lora_name input options
            if "lora_name" in required_inputs:
                lora_options = required_inputs["lora_name"]
                # lora_options is typically a list where first element contains the available options
                if isinstance(lora_options, list) and len(lora_options) > 0:
                    available_loras = lora_options[0]
                    if isinstance(available_loras, list):
                        for lora_name in available_loras:
                            # Remove file extension for display name
                            display_name = lora_name.replace('.safetensors', '').replace('.ckpt', '')
                            lora_info = LoRAInfo(
                                name=display_name,
                                file_path=lora_name,  # Keep full filename for ComfyUI
                                description=f"LoRA model: {display_name}",
                                tags=["lora", "style"]
                            )
                            loras.append(lora_info)
            
            return loras
            
        except Exception as e:
            # Fallback to empty list if server query fails
            print(f"Failed to query LoRAs from ComfyUI server: {e}")
            return []

    async def generate_image(
        self,
        workflow_template: Dict[str, Any],
        prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None,
        loras: Optional[List[str]] = None,
        width: int = 1024,
        height: int = 1024,
        enable_loras: bool = True
    ) -> Tuple[bytes, GenerationMetadata]:
        """Generate an image using the provided workflow template (workflow-agnostic)"""
        
        # Create a copy of the workflow template
        workflow = json.loads(json.dumps(workflow_template))
        
        # Generate seed if not provided
        if seed is None:
            seed = int(time.time()) % (2**32)
        
        # Apply prompts dynamically
        positive_node, negative_node = self._apply_prompt_to_workflow(workflow, prompt, negative_prompt)
        
        # Apply seed to sampling nodes
        self._apply_seed_to_workflow(workflow, seed)
        
        # Apply dimensions to latent nodes
        self._apply_dimensions_to_workflow(workflow, width, height)
        
        # Apply LoRAs if enabled (now async)
        await self._apply_loras_to_workflow(workflow, loras or [], enable_loras)
        
        start_time = time.time()
        
        # Queue the workflow
        prompt_id = await self.queue_prompt(workflow)
        
        # Wait for completion
        history = await self.wait_for_completion(prompt_id)
        
        generation_time = time.time() - start_time
        
        # Extract output information
        outputs = history.get("outputs", {})
        save_image_outputs = None
        
        # Find the SaveImage node output (node 9 in this workflow)
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
    
    async def get_available_loras(self) -> List:
        """Get list of available LoRA models from ComfyUI server"""
        return await self._get_available_loras_from_server()
