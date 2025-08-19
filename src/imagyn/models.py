"""
Configuration and data models for Imagyn MCP server
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Literal
from pathlib import Path


@dataclass
class ReplicateConfig:
    """Configuration for Replicate API"""
    api_key: str
    model_id: str
    default_speed_mode: str = "Extra Juiced 🔥 (more speed)"


@dataclass
class ImagynConfig:
    """Configuration for the Imagyn MCP server"""
    provider: Literal["comfyui", "replicate"]
    output_folder: str
    max_concurrent_generations: int = 3
    default_generation_timeout: int = 300
    http_timeout: float = 60.0
    websocket_timeout: float = 30.0
    # ComfyUI-specific settings (optional)
    comfyui_url: Optional[str] = None
    workflow_file: Optional[str] = None
    enable_loras: Optional[bool] = None
    # Replicate-specific settings (optional)
    replicate: Optional[ReplicateConfig] = None

    @classmethod
    def load_from_file(cls, config_path: str = "config.json") -> "ImagynConfig":
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Remove deprecated lora_folder_path if present for backward compatibility
        config_data.pop('lora_folder_path', None)
        
        # Handle replicate config
        replicate_data = config_data.get('replicate')
        if replicate_data:
            config_data['replicate'] = ReplicateConfig(**replicate_data)
        
        # Validate provider-specific configurations
        provider = config_data.get('provider')
        if provider == 'comfyui':
            if not config_data.get('comfyui_url'):
                raise ValueError("comfyui_url is required when provider is 'comfyui'")
            if not config_data.get('workflow_file'):
                raise ValueError("workflow_file is required when provider is 'comfyui'")
            if 'enable_loras' not in config_data:
                raise ValueError("enable_loras is required when provider is 'comfyui'")
        elif provider == 'replicate':
            if not config_data.get('replicate'):
                raise ValueError("replicate configuration is required when provider is 'replicate'")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return cls(**config_data)


@dataclass
class LoRAInfo:
    """Information about a LoRA model"""
    name: str
    file_path: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class GenerationMetadata:
    """Metadata for a generated image"""
    prompt: str
    negative_prompt: str = ""
    loras_used: List[str] = None
    generation_time: float = 0.0
    seed: int = 0
    width: int = 1024
    height: int = 1024
    steps: int = 20
    cfg: float = 3.5
    workflow_used: str = ""

    def __post_init__(self):
        if self.loras_used is None:
            self.loras_used = []


@dataclass
class GeneratedImage:
    """Represents a generated image with metadata"""
    image_id: str
    file_path: str
    metadata: GenerationMetadata
    created_at: str
    base64_data: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "image_id": self.image_id,
            "image_url": f"file://{self.file_path}",
            "image_base64": self.base64_data,
            "metadata": {
                "prompt": self.metadata.prompt,
                "negative_prompt": self.metadata.negative_prompt,
                "loras_used": self.metadata.loras_used,
                "generation_time": self.metadata.generation_time,
                "seed": self.metadata.seed,
                "width": self.metadata.width,
                "height": self.metadata.height,
                "steps": self.metadata.steps,
                "cfg": self.metadata.cfg,
                "workflow_used": self.metadata.workflow_used
            },
            "created_at": self.created_at
        }


@dataclass
class ComfyUIWorkflowRequest:
    """Request structure for ComfyUI workflow execution"""
    client_id: str
    prompt: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "prompt": self.prompt
        }
