#!/usr/bin/env python3
"""
Simple stdio-based MCP server for Imagyn
This uses the standard stdio transport which is more compatible with most MCP clients
"""

import asyncio
import json
import logging
import sys
import platform
import os
import time
import httpx
import uuid
import websockets
import base64
from pathlib import Path
from typing import Any, Dict, Optional

# Fal.ai import (will be conditionally used)
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False
    fal_client = None

# Fix for Windows asyncio issues - must be done before any asyncio operations
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure we're using the virtual environment Python
script_dir = Path(__file__).parent
venv_path = script_dir / "imagyn_venv"
if venv_path.exists():
    # Add virtual environment site-packages to Python path
    site_packages = venv_path / "Lib" / "site-packages"
    if site_packages.exists():
        sys.path.insert(0, str(site_packages))

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Set up logging to stderr to avoid interfering with stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("imagyn-mcp")

# Global variables for server state
server_config = None
server_storage = None
server_workflow = None

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Config file not found: {config_path}")
            return None
            
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Normalize provider name to lowercase
        if 'provider' in config:
            config['provider'] = config['provider'].lower()
        
        logger.info(f"Loaded config from {config_path}")
        logger.info(f"Provider: {config.get('provider', 'not specified')}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

def load_workflow(workflow_path: str) -> Dict[str, Any]:
    """Load workflow template"""
    try:
        workflow_file = Path(workflow_path)
        if not workflow_file.exists():
            logger.error(f"Workflow file not found: {workflow_path}")
            return None
            
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        logger.info(f"Loaded workflow from {workflow_path}")
        return workflow
    except Exception as e:
        logger.error(f"Failed to load workflow: {e}")
        return None

# Create the server
server = Server("imagyn-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    global server_config
    
    tools = [
        types.Tool(
            name="get_server_status",
            description="Get the current status of the Imagyn MCP server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="test_connection", 
            description="Test the MCP connection",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
    
    # Add generate_image tool with provider-specific description
    provider = server_config.get('provider', 'comfyui') if server_config else 'comfyui'
    
    generate_tool = types.Tool(
        name="generate_image",
        description=f"Generate an image using {provider.upper()} with the specified prompt",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt for image generation"
                },
                "negative_prompt": {
                    "type": "string", 
                    "description": "Negative prompt to avoid certain elements (ComfyUI only)"
                },
                "width": {
                    "type": "integer",
                    "description": "Image width in pixels",
                    "minimum": 64,
                    "maximum": 2048
                },
                "height": {
                    "type": "integer",
                    "description": "Image height in pixels",
                    "minimum": 64,
                    "maximum": 2048
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio for the image (e.g., '1:1', '16:9', '9:16') - Replicate models only",
                    "enum": ["1:1", "16:9", "9:16", "21:9", "2:3", "3:2", "4:5", "5:4"]
                },
                "seed": {
                    "type": "integer",
                    "description": "Seed for reproducible generation (optional)",
                    "minimum": 0
                },
                "guidance": {
                    "type": "number",
                    "description": "Guidance scale for generation (typically 1-20, default varies by model)",
                    "minimum": 1,
                    "maximum": 20
                },
                "num_inference_steps": {
                    "type": "integer",
                    "description": "Number of inference steps (more steps = higher quality, slower generation)",
                    "minimum": 1,
                    "maximum": 50
                },
                "go_fast": {
                    "type": "boolean",
                    "description": "Enable fast mode for quicker generation (Replicate models only)"
                },
                "output_format": {
                    "type": "string",
                    "description": "Output image format",
                    "enum": ["png", "jpg", "webp"]
                },
                "output_quality": {
                    "type": "integer",
                    "description": "Output quality for compressed formats (1-100)",
                    "minimum": 1,
                    "maximum": 100
                },
                "image_size": {
                    "type": "string",
                    "description": "Image size preset (Fal.ai models only)",
                    "enum": ["square", "square_hd", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"]
                },
                "num_images": {
                    "type": "integer",
                    "description": "Number of images to generate (Fal.ai models only, 1-4)",
                    "minimum": 1,
                    "maximum": 4
                },
                "enable_safety_checker": {
                    "type": "boolean",
                    "description": "Enable safety checker for content filtering (Fal.ai models only)"
                }
            },
            "required": ["prompt"]
        }
    )
    
    tools.append(generate_tool)
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    try:
        if name == "get_server_status":
            return await get_server_status()
        elif name == "test_connection":
            return await test_connection()
        elif name == "generate_image":
            return await generate_image(arguments)
        else:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return [types.TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    except Exception as e:
        error_msg = f"Error handling tool {name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_server_status() -> list[types.TextContent]:
    """Get server status"""
    global server_config, server_storage, server_workflow
    
    provider = server_config.get('provider', 'comfyui') if server_config else 'comfyui'
    
    status = {
        "status": "running",
        "server_name": "Imagyn MCP Server (stdio)",
        "version": "0.1.0",
        "provider": provider,
        "config_loaded": server_config is not None,
        "workflow_loaded": server_workflow is not None,
    }
    
    # Provider-specific status
    if provider == 'comfyui':
        status["comfyui_url"] = server_config.get("comfyui_url", "Not configured") if server_config else "Not configured"
        status["workflow_file"] = server_config.get("workflow_file", "Not configured") if server_config else "Not configured"
        status["enable_loras"] = server_config.get("enable_loras", False) if server_config else False
    elif provider == 'replicate':
        if server_config and server_config.get('replicate'):
            status["replicate_model"] = server_config['replicate'].get('model_id', 'Not configured')
            status["replicate_api_key"] = "***configured***" if server_config['replicate'].get('api_key') else "Not configured"
            # Remove speed_mode since it's model-dependent now
        else:
            status["replicate"] = "Not configured"
    elif provider == 'fal':
        if server_config and server_config.get('fal'):
            status["fal_model"] = server_config['fal'].get('model_id', 'Not configured')
            status["fal_api_key"] = "***configured***" if server_config['fal'].get('api_key') else "Not configured"
            status["fal_client_available"] = FAL_AVAILABLE
        else:
            status["fal"] = "Not configured"
    
    # Add timeout configurations if config is loaded
    if server_config:
        status["timeouts"] = {
            "http_timeout": server_config.get("http_timeout", 60.0),
            "websocket_timeout": server_config.get("websocket_timeout", 30.0),
            "generation_timeout": server_config.get("default_generation_timeout", 300)
        }
    
    return [types.TextContent(
        type="text", 
        text=json.dumps(status, indent=2)
    )]

async def test_connection() -> list[types.TextContent]:
    """Test connection"""
    return [types.TextContent(
        type="text",
        text="MCP server is responding correctly. Connection test successful."
    )]

async def generate_image(arguments: dict) -> list[types.TextContent | types.ImageContent]:
    """Generate image using the configured provider"""
    global server_config, server_workflow
    
    prompt = arguments.get("prompt", "")
    negative_prompt = arguments.get("negative_prompt", "")
    width = arguments.get("width", 1024)
    height = arguments.get("height", 1024)
    aspect_ratio = arguments.get("aspect_ratio")
    seed = arguments.get("seed", None)
    guidance = arguments.get("guidance")
    num_inference_steps = arguments.get("num_inference_steps")
    go_fast = arguments.get("go_fast")
    output_format = arguments.get("output_format")
    output_quality = arguments.get("output_quality")
    image_size = arguments.get("image_size")
    num_images = arguments.get("num_images")
    enable_safety_checker = arguments.get("enable_safety_checker")
    
    if not prompt.strip():
        return [types.TextContent(
            type="text",
            text="Error: Prompt cannot be empty."
        )]
    
    if not server_config:
        return [types.TextContent(
            type="text",
            text="Error: Server configuration not loaded. Cannot generate images."
        )]
    
    provider = server_config.get('provider', 'comfyui').lower()
    
    if provider == 'comfyui':
        return await generate_image_comfyui(prompt, negative_prompt, width, height, seed)
    elif provider == 'replicate':
        return await generate_image_replicate(
            prompt, negative_prompt, width, height, aspect_ratio, seed, 
            guidance, num_inference_steps, go_fast, output_format, output_quality
        )
    elif provider == 'fal':
        return await generate_image_fal(
            prompt, negative_prompt, width, height, seed, guidance, 
            num_inference_steps, image_size, num_images, enable_safety_checker
        )
    else:
        return [types.TextContent(
            type="text",
            text=f"Error: Unsupported provider '{provider}'. Supported providers: comfyui, replicate, fal"
        )]


async def generate_image_comfyui(prompt: str, negative_prompt: str, width: int, height: int, seed: Optional[int]) -> list[types.TextContent | types.ImageContent]:
    """Generate image using ComfyUI"""
    import time
    import httpx
    import uuid
    import websockets
    import base64
    from pathlib import Path
    
    if not server_workflow:
        return [types.TextContent(
            type="text",
            text="Error: Workflow template not loaded. Cannot generate images with ComfyUI."
        )]
    
    try:
        base_url = server_config.get("comfyui_url", "http://localhost:8188").rstrip('/')
        client_id = str(uuid.uuid4())
        
        # Get timeout configurations from config
        http_timeout = server_config.get("http_timeout", 60.0)
        websocket_timeout = server_config.get("websocket_timeout", 30.0)
        generation_timeout = server_config.get("default_generation_timeout", 300)
        
        # Test connection
        async with httpx.AsyncClient(timeout=http_timeout) as client:
            try:
                response = await client.get(f"{base_url}/system_stats")
                if response.status_code != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Cannot connect to ComfyUI at {base_url}"
                    )]
            except Exception as e:
                return [types.TextContent(
                    type="text", 
                    text=f"Error: Cannot connect to ComfyUI at {base_url}: {str(e)}"
                )]
            
            # Prepare workflow
            workflow = json.loads(json.dumps(server_workflow))
            
            # Set the prompt (node 45 is CLIP Text Encode)
            if "45" in workflow:  # Positive prompt node
                workflow["45"]["inputs"]["text"] = prompt
            
            # Set negative prompt (this workflow uses ConditioningZeroOut instead of negative prompt)
            # We'll keep the existing structure for now
                
            # Set seed (node 31 is KSampler)
            if seed is None:
                seed = int(time.time()) % (2**32)
            if "31" in workflow:  # KSampler node
                workflow["31"]["inputs"]["seed"] = seed
                
            # Set dimensions (node 27 is EmptySD3LatentImage)
            if "27" in workflow:  # Empty latent image node
                workflow["27"]["inputs"]["width"] = width
                workflow["27"]["inputs"]["height"] = height
            
            logger.info(f"Generating image with ComfyUI: {prompt[:100]}...")
            start_time = time.time()
            
            # Queue the workflow
            prompt_request = {
                "client_id": client_id,
                "prompt": workflow
            }
            
            response = await client.post(f"{base_url}/prompt", json=prompt_request)
            response.raise_for_status()
            result = response.json()
            prompt_id = result["prompt_id"]
            
            # Wait for completion via WebSocket
            ws_url = base_url.replace('http', 'ws') + f"/ws?clientId={client_id}"
            
            async with websockets.connect(ws_url) as websocket:
                start_ws_time = time.time()
                
                while time.time() - start_ws_time < generation_timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=websocket_timeout)
                        data = json.loads(message)
                        
                        if data["type"] == "executing":
                            executing_data = data["data"]
                            if executing_data["node"] is None and executing_data["prompt_id"] == prompt_id:
                                # Execution completed
                                break
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        return [types.TextContent(
                            type="text",
                            text="Error: WebSocket connection closed during generation"
                        )]
            
            # Get history and download image
            response = await client.get(f"{base_url}/history/{prompt_id}")
            response.raise_for_status()
            history = response.json()
            
            prompt_history = history.get(prompt_id, {})
            outputs = prompt_history.get("outputs", {})
            
            # Find the SaveImage node output
            save_image_outputs = None
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    save_image_outputs = node_output["images"]
                    break
            
            if not save_image_outputs:
                return [types.TextContent(
                    type="text",
                    text="Error: No image output found in workflow execution"
                )]
            
            # Download the first image
            image_info = save_image_outputs[0]
            params = {
                "filename": image_info["filename"],
                "type": image_info.get("type", "output")
            }
            if image_info.get("subfolder"):
                params["subfolder"] = image_info["subfolder"]
            
            response = await client.get(f"{base_url}/view", params=params)
            response.raise_for_status()
            image_data = response.content
            
            generation_time = time.time() - start_time
            
            # Store image locally
            output_dir = Path(server_config.get("output_folder", "output"))
            output_dir.mkdir(exist_ok=True)
            
            # Create unique filename
            image_id = f"img_{int(time.time())}_{seed}"
            image_path = output_dir / f"{image_id}.png"
            
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            # Convert to base64 for MCP response
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            logger.info(f"Image generated successfully: {image_id} in {generation_time:.2f}s")
            
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ **Image Generated Successfully with ComfyUI!**\n\n"
                         f"**Image ID:** {image_id}\n"
                         f"**Prompt:** {prompt}\n" 
                         f"**Dimensions:** {width}×{height}\n"
                         f"**Seed:** {seed}\n"
                         f"**Generation Time:** {generation_time:.2f}s\n"
                         f"**Saved to:** {image_path}\n\n"
                         f"The image has been generated and is displayed below:"
                ),
                types.ImageContent(
                    type="image",
                    data=base64_data,
                    mimeType="image/png"
                )
            ]
            
    except Exception as e:
        logger.error(f"ComfyUI image generation failed: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"❌ **ComfyUI image generation failed:** {str(e)}"
        )]


async def generate_image_replicate(
    prompt: str, negative_prompt: str, width: int, height: int, aspect_ratio: str,
    seed: Optional[int], guidance: Optional[float], num_inference_steps: Optional[int],
    go_fast: Optional[bool], output_format: Optional[str], output_quality: Optional[int]
) -> list[types.TextContent | types.ImageContent]:
    """Generate image using Replicate"""
    import time
    import httpx
    import base64
    from pathlib import Path
    
    replicate_config = server_config.get('replicate')
    if not replicate_config:
        return [types.TextContent(
            type="text",
            text="Error: Replicate configuration not found in config.json"
        )]
    
    api_key = replicate_config.get('api_key')
    model_id = replicate_config.get('model_id')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text="Error: Replicate API key not configured"
        )]
    
    if not model_id:
        return [types.TextContent(
            type="text",
            text="Error: Replicate model ID not configured"
        )]
    
    try:
        start_time = time.time()
        
        # Build intelligent input based on model and provided parameters
        input_data = {"prompt": prompt}
        
        # Handle different model formats and their expected parameters
        model_lower = model_id.lower()
        
        # Check if it's a black-forest-labs model (newer format)
        if "black-forest-labs" in model_lower or "flux-dev" in model_lower:
            # black-forest-labs/flux-dev model parameters
            if go_fast is not None:
                input_data["go_fast"] = go_fast
            else:
                input_data["go_fast"] = True  # Default to fast mode
                
            if guidance is not None:
                input_data["guidance"] = guidance
            else:
                input_data["guidance"] = 3.5  # Default guidance
                
            if aspect_ratio:
                input_data["aspect_ratio"] = aspect_ratio
            else:
                # Convert width/height to aspect ratio
                if width == height:
                    input_data["aspect_ratio"] = "1:1"
                elif width > height:
                    if width / height >= 1.7:
                        input_data["aspect_ratio"] = "16:9"
                    else:
                        input_data["aspect_ratio"] = "3:2"
                else:
                    if height / width >= 1.7:
                        input_data["aspect_ratio"] = "9:16"
                    else:
                        input_data["aspect_ratio"] = "2:3"
                        
            # Calculate megapixels from aspect ratio or dimensions
            if aspect_ratio:
                input_data["megapixels"] = "1"  # Standard 1MP for aspect ratio models
            else:
                mp = (width * height) / 1000000
                input_data["megapixels"] = str(max(1, int(mp)))
                
            if num_inference_steps is not None:
                input_data["num_inference_steps"] = num_inference_steps
            else:
                input_data["num_inference_steps"] = 28  # Default steps
                
            input_data["num_outputs"] = 1  # Always single output
            
            if output_format:
                input_data["output_format"] = output_format
            else:
                input_data["output_format"] = "webp"  # Default format
                
            if output_quality is not None:
                input_data["output_quality"] = output_quality
            else:
                input_data["output_quality"] = 80  # Default quality
                
            input_data["prompt_strength"] = 0.8  # Default prompt strength
            
        else:
            # Older model format (like prunaai/flux.1-dev) - use legacy parameters
            if negative_prompt:
                input_data["prompt"] = f"{prompt}. Avoid: {negative_prompt}"
                
            input_data["width"] = width
            input_data["height"] = height
            
            # Check if model supports speed_mode
            if "speed_mode" in model_lower or "prunaai" in model_lower:
                speed_mode = replicate_config.get('default_speed_mode', 'Extra Juiced 🔥 (more speed)')
                input_data["speed_mode"] = speed_mode
        
        # Add seed if provided
        if seed is not None:
            input_data["seed"] = seed
        else:
            seed = int(time.time()) % (2**31)
            input_data["seed"] = seed
        
        http_timeout = server_config.get("http_timeout", 60.0)
        generation_timeout = server_config.get("default_generation_timeout", 300)
        
        async with httpx.AsyncClient(
            headers={"Authorization": f"Token {api_key}"},
            timeout=generation_timeout
        ) as client:
            
            logger.info(f"Generating image with Replicate model {model_id}: {prompt[:100]}...")
            logger.info(f"Input parameters: {input_data}")
            
            # Use the simplified run format for newer models
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                json={
                    "input": input_data,
                    **_parse_model_reference(model_id)
                }
            )
            prediction_response.raise_for_status()
            
            prediction = prediction_response.json()
            prediction_id = prediction["id"]
            
            # Wait for completion
            start_poll_time = time.time()
            while time.time() - start_poll_time < generation_timeout:
                status_response = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}"
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data["status"]
                
                if status == "succeeded":
                    # Get the output URL
                    output_url = status_data["output"]
                    
                    # Handle different output formats
                    if isinstance(output_url, list) and output_url:
                        # Multiple outputs, take the first one
                        output_url = output_url[0]
                    elif isinstance(output_url, str):
                        # Single output URL
                        pass
                    else:
                        return [types.TextContent(
                            type="text",
                            text=f"Error: Unexpected output format: {type(output_url)}"
                        )]
                    
                    # Download the image
                    image_response = await httpx.AsyncClient().get(output_url)
                    image_response.raise_for_status()
                    image_data = image_response.content
                    
                    generation_time = time.time() - start_time
                    
                    # Store image locally
                    output_dir = Path(server_config.get("output_folder", "output"))
                    output_dir.mkdir(exist_ok=True)
                    
                    # Create unique filename with appropriate extension
                    file_extension = output_format or "webp"
                    if file_extension == "jpg":
                        file_extension = "jpeg"
                    image_id = f"img_{int(time.time())}_{seed}"
                    image_path = output_dir / f"{image_id}.{file_extension}"
                    
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                    
                    # Convert to base64 for MCP response
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    logger.info(f"Image generated successfully with Replicate: {image_id} in {generation_time:.2f}s")
                    
                    # Build parameter summary
                    param_summary = []
                    for key, value in input_data.items():
                        if key != "prompt":
                            param_summary.append(f"{key}: {value}")
                    
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✅ **Image Generated Successfully with Replicate!**\n\n"
                                 f"**Image ID:** {image_id}\n"
                                 f"**Prompt:** {prompt}\n"
                                 f"**Model:** {model_id}\n"
                                 f"**Parameters:** {', '.join(param_summary)}\n"
                                 f"**Seed:** {seed}\n"
                                 f"**Generation Time:** {generation_time:.2f}s\n"
                                 f"**Saved to:** {image_path}\n\n"
                                 f"The image has been generated and is displayed below:"
                        ),
                        types.ImageContent(
                            type="image",
                            data=base64_data,
                            mimeType=f"image/{file_extension}"
                        )
                    ]
                    
                elif status == "failed":
                    error_message = status_data.get("error", "Unknown error occurred")
                    return [types.TextContent(
                        type="text",
                        text=f"❌ **Replicate generation failed:** {error_message}"
                    )]
                
                elif status in ["starting", "processing"]:
                    # Wait before checking again
                    await asyncio.sleep(2)
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ **Unexpected status:** {status}"
                    )]
            
            # Timeout
            return [types.TextContent(
                type="text",
                text=f"❌ **Generation timeout:** Image generation took longer than {generation_timeout} seconds"
            )]
            
    except Exception as e:
        logger.error(f"Replicate image generation failed: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"❌ **Replicate image generation failed:** {str(e)}"
        )]



async def generate_image_fal(
    prompt: str, negative_prompt: str, width: int, height: int, seed: Optional[int],
    guidance: Optional[float], num_inference_steps: Optional[int], image_size: Optional[str],
    num_images: Optional[int], enable_safety_checker: Optional[bool]
) -> list[types.TextContent | types.ImageContent]:
    """Generate image using Fal.ai"""
    import time
    import asyncio
    import base64
    from pathlib import Path
    
    if not FAL_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Error: fal_client library not installed. Please install it with: pip install fal-client"
        )]
    
    fal_config = server_config.get('fal')
    if not fal_config:
        return [types.TextContent(
            type="text",
            text="Error: Fal.ai configuration not found in config.json"
        )]
    
    api_key = fal_config.get('api_key')
    model_id = fal_config.get('model_id')
    
    if not api_key:
        return [types.TextContent(
            type="text",
            text="Error: Fal.ai API key not configured"
        )]
    
    if not model_id:
        return [types.TextContent(
            type="text",
            text="Error: Fal.ai model ID not configured"
        )]
    
    try:
        # Set the API key as environment variable (required by fal_client)
        import os
        os.environ['FAL_KEY'] = api_key
        
        start_time = time.time()
        
        # Build input arguments based on model capabilities
        arguments = {"prompt": prompt}
        
        # Add optional parameters if provided
        if seed is not None:
            arguments["seed"] = seed
        else:
            seed = int(time.time()) % (2**31)
            arguments["seed"] = seed
        
        # Image size handling - convert to Fal.ai format
        if image_size:
            arguments["image_size"] = image_size
        elif width and height:
            # Try to map width/height to Fal.ai image size presets
            if width == height:
                if width <= 512:
                    arguments["image_size"] = "square"
                else:
                    arguments["image_size"] = "square_hd"
            elif width > height:
                if width / height >= 1.7:
                    arguments["image_size"] = "landscape_16_9"
                else:
                    arguments["image_size"] = "landscape_4_3"
            else:
                if height / width >= 1.7:
                    arguments["image_size"] = "portrait_16_9"
                else:
                    arguments["image_size"] = "portrait_4_3"
        
        # Add other optional parameters with sensible defaults
        if guidance is not None:
            arguments["guidance_scale"] = guidance
        
        if num_inference_steps is not None:
            arguments["num_inference_steps"] = num_inference_steps
        
        if num_images is not None and num_images > 1:
            arguments["num_images"] = min(num_images, 4)  # Cap at 4 images
        else:
            arguments["num_images"] = 1
        
        if enable_safety_checker is not None:
            arguments["enable_safety_checker"] = enable_safety_checker
        
        # Add negative prompt if provided (for models that support it)
        if negative_prompt:
            arguments["negative_prompt"] = negative_prompt
        
        logger.info(f"Generating image with Fal.ai model {model_id}: {prompt[:100]}...")
        logger.info(f"Arguments: {arguments}")
        
        # Track progress
        progress_logs = []
        
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    progress_logs.append(log["message"])
                    logger.info(f"Fal.ai progress: {log['message']}")
        
        # Subscribe to the model with progress tracking
        result = fal_client.subscribe(
            model_id,
            arguments=arguments,
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        generation_time = time.time() - start_time
        
        logger.info(f"Raw Fal.ai result: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Handle the result
        if not result:
            return [types.TextContent(
                type="text",
                text="Error: No result returned from Fal.ai"
            )]
        
        # Extract images from result - Fal.ai returns images in a specific format
        images = []
        if "images" in result:
            # Standard format: {"images": [{"url": "...", "width": 1024, "height": 1024}]}
            images = [img["url"] for img in result["images"] if "url" in img]
        elif "image" in result:
            # Alternative format: {"image": {"url": "..."}}
            if isinstance(result["image"], dict) and "url" in result["image"]:
                images = [result["image"]["url"]]
            elif isinstance(result["image"], str):
                images = [result["image"]]
        elif "url" in result:
            # Direct URL format: {"url": "..."}
            images = [result["url"]]
        
        if not images:
            return [types.TextContent(
                type="text",
                text=f"Error: No image URLs found in result.\n"
                     f"Result structure: {list(result.keys())}\n"
                     f"Full result: {str(result)[:500]}..."
            )]
        
        # Process the images
        generated_images = []
        text_responses = []
        
        # Create a summary first
        image_count = len(images)
        summary_params = []
        for key, value in arguments.items():
            if key != "prompt":
                summary_params.append(f"{key}: {value}")
        
        summary_text = (
            f"✅ **Image{'s' if image_count > 1 else ''} Generated Successfully with Fal.ai!**\n\n"
            f"**Generated {image_count} image{'s' if image_count > 1 else ''}**\n"
            f"**Prompt:** {prompt}\n"
            f"**Model:** {model_id}\n"
            f"**Parameters:** {', '.join(summary_params)}\n"
            f"**Seed:** {seed}\n"
            f"**Generation Time:** {generation_time:.2f}s\n"
        )
        
        # Add progress logs if any
        if progress_logs:
            summary_text += f"**Progress:** {' → '.join(progress_logs[-3:])}\n"  # Show last 3 progress messages
        
        # Store images locally and prepare for response
        output_dir = Path(server_config.get("output_folder", "output"))
        output_dir.mkdir(exist_ok=True)
        
        for i, image_url in enumerate(images):
            try:
                # Download the image
                import httpx
                async with httpx.AsyncClient() as client:
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()
                    image_data = image_response.content
                
                # Save locally
                image_id = f"img_{int(time.time())}_{seed}_{i}" if image_count > 1 else f"img_{int(time.time())}_{seed}"
                image_path = output_dir / f"{image_id}.png"
                
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                # Convert to base64 for MCP response
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                generated_images.append(types.ImageContent(
                    type="image",
                    data=base64_data,
                    mimeType="image/png"
                ))
                
                if i == 0:  # Add path info to summary for first image
                    summary_text += f"**Saved to:** {image_path}\n"
                
                logger.info(f"Image {i+1}/{image_count} processed: {image_id}")
                
            except Exception as e:
                logger.error(f"Error processing image {i+1}: {e}")
                continue
        
        if not generated_images:
            return [types.TextContent(
                type="text",
                text="Error: Failed to process any images from Fal.ai response"
            )]
        
        summary_text += f"\nThe image{'s are' if image_count > 1 else ' is'} displayed below:"
        
        # Return text summary followed by all images
        response = [types.TextContent(type="text", text=summary_text)]
        response.extend(generated_images)
        
        return response
        
    except Exception as e:
        logger.error(f"Fal.ai image generation failed: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"❌ **Fal.ai image generation failed:** {str(e)}"
        )]


def _parse_model_reference(model_id: str) -> dict:
    """Parse model reference into owner/name or version format"""
    if ":" in model_id:
        # Format: owner/name:version
        model_parts = model_id.split(":")
        if len(model_parts) == 2:
            return {"version": model_parts[1]}
    
    # Format: owner/name (use latest version)
    return {"model": model_id}

async def main():
    """Main entry point"""
    global server_config, server_workflow
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Load configuration
    config_path = os.getenv("IMAGYN_CONFIG", "config.json")
    logger.info(f"Loading config from: {config_path}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    server_config = load_config(config_path)
    if server_config:
        provider = server_config.get('provider', 'comfyui').lower()
        
        # Only load workflow if using ComfyUI
        if provider == 'comfyui':
            workflow_file = server_config.get("workflow_file")
            if workflow_file:
                server_workflow = load_workflow(workflow_file)
            else:
                logger.warning("ComfyUI provider selected but no workflow_file specified")
        elif provider == 'replicate':
            logger.info("Replicate provider selected - workflow not needed")
            server_workflow = None
        elif provider == 'fal':
            logger.info("Fal.ai provider selected - workflow not needed")
            server_workflow = None
            # Check if fal_client is available
            if not FAL_AVAILABLE:
                logger.warning("Fal.ai provider selected but fal_client library not installed")
        else:
            logger.error(f"Unknown provider: {provider}")
    
    logger.info("Starting MCP server...")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP server streams established")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="imagyn-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)
