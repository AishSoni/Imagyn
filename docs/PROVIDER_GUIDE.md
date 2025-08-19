# Imagyn MCP Server - Provider Guide

This guide explains how to use each of the three supported image generation providers in Imagyn MCP Server.

## Overview

Imagyn supports three different image generation providers:

1. **ComfyUI** - Local/self-hosted workflows with full customization
2. **Replicate** - Cloud-based API with hosted models
3. **Fal.ai** - Fast cloud-based API with optimized models

## Provider Comparison

| Feature | ComfyUI | Replicate | Fal.ai |
|---------|---------|-----------|--------|
| **Hosting** | Self-hosted | Cloud | Cloud |
| **API Key Required** | ❌ | ✅ | ✅ |
| **Custom Workflows** | ✅ | ❌ | ❌ |
| **LoRA Support** | ✅ | ❌ | ❌ |
| **Multiple Images** | ❌ | ✅ | ✅ |
| **Image Editing** | ✅ | ❌ | ❌ |
| **Speed** | Variable | Fast | Very Fast |
| **Cost** | Free (your hardware) | Pay per use | Pay per use |
| **Model Selection** | Any compatible | Model marketplace | Curated models |

## Configuration

### ComfyUI Provider

```json
{
  "provider": "comfyui",
  "comfyui_url": "http://localhost:8188",
  "workflow_file": "workflows/fluxkrea.json",
  "enable_loras": true,
  "output_folder": "output",
  "max_concurrent_generations": 3,
  "default_generation_timeout": 300,
  "http_timeout": 60.0,
  "websocket_timeout": 30.0
}
```

**Requirements:**
- ComfyUI server running locally or accessible via network
- Workflow JSON file exported from ComfyUI
- Optional: LoRA models for style customization

**Best for:**
- Full control over generation process
- Custom workflows and advanced techniques
- LoRA model experimentation
- No per-generation costs

### Replicate Provider

```json
{
  "provider": "replicate",
  "output_folder": "output",
  "max_concurrent_generations": 3,
  "default_generation_timeout": 300,
  "http_timeout": 60.0,
  "replicate": {
    "api_key": "r8_your_replicate_api_key_here",
    "model_id": "black-forest-labs/flux-dev"
  }
}
```

**Requirements:**
- Replicate API key (get from https://replicate.com)
- Choose from available models on Replicate

**Popular Models:**
- `black-forest-labs/flux-dev` - High-quality general purpose
- `prunaai/flux.1-dev` - Faster inference with speed modes
- `bytedance/sdxl-lightning-4step` - Very fast generation

**Best for:**
- Quick setup without local infrastructure
- Access to latest models
- Reliable cloud hosting
- Multiple image generation

### Fal.ai Provider

```json
{
  "provider": "fal",
  "output_folder": "output",
  "max_concurrent_generations": 3,
  "default_generation_timeout": 300,
  "http_timeout": 60.0,
  "fal": {
    "api_key": "your_fal_api_key_here",
    "model_id": "fal-ai/flux-1/krea"
  }
}
```

**Requirements:**
- Fal.ai API key (get from https://fal.ai)
- Choose from available models on Fal.ai

**Popular Models:**
- `fal-ai/flux-1/krea` - Fast FLUX model optimized for speed
- `fal-ai/flux-1/dev` - High-quality FLUX development model
- `fal-ai/flux-1/schnell` - Ultra-fast FLUX model

**Best for:**
- Fastest generation times
- Optimized model inference
- Multiple image generation
- Built-in safety features

## Usage Examples

### Basic Generation

```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A serene mountain landscape at sunset, oil painting style"
  }
}
```

### Advanced Parameters

#### ComfyUI
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A cyberpunk cityscape at night",
    "negative_prompt": "blurry, low quality, distorted",
    "width": 1024,
    "height": 1024,
    "seed": 42
  }
}
```

#### Replicate
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A majestic eagle soaring over mountains",
    "aspect_ratio": "16:9",
    "guidance": 7.5,
    "num_inference_steps": 28,
    "go_fast": true,
    "output_format": "webp",
    "output_quality": 90
  }
}
```

#### Fal.ai
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A beautiful garden with colorful flowers",
    "image_size": "square_hd",
    "num_images": 2,
    "guidance": 7.5,
    "num_inference_steps": 28,
    "enable_safety_checker": true
  }
}
```

## Parameter Guide

### Common Parameters (All Providers)
- `prompt` (required): Text description of the image
- `seed` (optional): Random seed for reproducible results

### ComfyUI Specific
- `negative_prompt`: Text to avoid in the image
- `width`, `height`: Exact pixel dimensions
- `loras`: Array of LoRA model names (if enabled)

### Replicate Specific
- `aspect_ratio`: Predefined aspect ratios (1:1, 16:9, 9:16, etc.)
- `go_fast`: Enable faster generation (newer models)
- `output_format`: Image format (png, jpg, webp)
- `output_quality`: Quality for compressed formats (1-100)

### Fal.ai Specific
- `image_size`: Size presets (square, square_hd, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9)
- `num_images`: Generate multiple images (1-4)
- `enable_safety_checker`: Content filtering
- `negative_prompt`: Text to avoid (supported by most models)

### Shared Cloud Parameters
- `guidance`: Guidance scale (1-20, typically 3-12)
- `num_inference_steps`: Quality vs speed trade-off (1-50)

## Getting API Keys

### Replicate
1. Visit https://replicate.com
2. Sign up for an account
3. Go to Account Settings > API Tokens
4. Create a new token
5. Copy the token (starts with `r8_`)

### Fal.ai
1. Visit https://fal.ai
2. Sign up for an account
3. Go to the API section
4. Generate an API key
5. Copy the API key

## Troubleshooting

### ComfyUI Issues
- Ensure ComfyUI server is running and accessible
- Check workflow JSON is valid and compatible
- Verify all required nodes are installed in ComfyUI

### Replicate Issues
- Verify API key is correct and has sufficient credits
- Check if the model ID exists and is accessible
- Some older models may have different parameter requirements

### Fal.ai Issues
- Verify API key is correct and account is active
- Check if the model ID is valid
- Ensure fal-client library is installed (`pip install fal-client`)

### General Issues
- Check network connectivity
- Verify configuration file syntax
- Monitor generation timeouts
- Check output folder permissions

## Performance Tips

### Speed Optimization
- **Fal.ai**: Generally fastest, optimized infrastructure
- **Replicate**: Use `go_fast: true` on supported models
- **ComfyUI**: Optimize workflows, use appropriate samplers

### Quality vs Speed
- Higher `num_inference_steps` = better quality, slower generation
- Lower `guidance` values can be faster
- Image size affects generation time significantly

### Cost Optimization
- **ComfyUI**: Free after initial setup costs
- **Replicate/Fal.ai**: Monitor usage, use appropriate quality settings
- Generate multiple variations with different seeds rather than re-running

## Model Recommendations

### For Photorealistic Images
- Replicate: `black-forest-labs/flux-dev`
- Fal.ai: `fal-ai/flux-1/dev`

### For Speed
- Replicate: `prunaai/flux.1-dev` with speed mode
- Fal.ai: `fal-ai/flux-1/schnell`

### For Artistic Styles
- ComfyUI: Custom workflows with LoRAs
- Replicate: Specialized art models

### For Multiple Variations
- Fal.ai: Use `num_images` parameter
- Replicate: Some models support multiple outputs
