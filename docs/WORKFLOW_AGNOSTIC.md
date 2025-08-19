# Workflow-Agnostic Image Generation System

## Overview
The Imagyn MCP server now supports workflow-agnostic image generation, meaning it can work with any ComfyUI workflow without requiring hardcoded node IDs.

## Key Features

### 1. Dynamic Node Discovery
The system automatically finds nodes by their `class_type` instead of relying on fixed node IDs:

- **CLIPTextEncode**: For positive and negative prompts
- **KSampler/KSamplerAdvanced**: For seed and sampling parameters  
- **EmptyLatentImage/EmptySD3LatentImage/EmptyFluxLatentImage**: For image dimensions
- **LoraLoader**: For LoRA model application

### 2. Intelligent Prompt Handling
- Automatically detects positive and negative prompt nodes
- Uses content analysis to distinguish between positive/negative prompts
- Falls back to positional logic (first node = positive, second = negative)
- Combines negative prompt with positive if no dedicated negative node exists

### 3. Smart LoRA Integration
- **Configurable**: Respects `enable_loras` setting in config.json
- **Auto-selection**: Automatically picks available LoRAs if none specified
- **Validation**: Checks if requested LoRAs exist in the configured directory
- **Fallback**: Uses alternative LoRAs if requested ones aren't found

### 4. Flexible Dimension Handling
Supports multiple latent image node types:
- EmptyLatentImage (SD 1.5/2.x)
- EmptySD3LatentImage (SD 3.x)
- EmptyFluxLatentImage (Flux models)

### 5. Universal Seed Application
Finds and applies seeds to any sampling node type:
- KSampler
- KSamplerAdvanced  
- SamplerCustom

## Current Workflow Compatibility

### Tested Workflow: `workflows/fluxkrea.json`
- **Model**: Flux-based workflow
- **Nodes Found**:
  - CLIPTextEncode: Node 45 (positive prompt)
  - KSampler: Node 31 (sampling)
  - EmptySD3LatentImage: Node 27 (dimensions)
  - LoraLoader: None (workflow doesn't include LoRA support)

### Available LoRAs
Your system has these LoRAs available:
- 3D_Chibi_lora_weights
- extra_kontext_lora
- flux-kontext-dev-jpeg-compression-fix-lora
- flux-uncensored
- ghibliStyle_kontext_byJaneB

## Configuration

### config.json Settings
```json
{
  "enable_loras": true,  // Enable/disable LoRA usage
  "lora_folder_path": "E:\\AI\\ComfyUI\\models\\loras\\",
  "comfyui_url": "http://localhost:8000",
  "workflow_file": "workflows/fluxkrea.json"
}
```

## Usage Examples

### Basic Image Generation
```python
await generate_image(
    prompt="a beautiful sunset over mountains",
    width=1024,
    height=768
)
```

### With Negative Prompt
```python
await generate_image(
    prompt="a beautiful sunset over mountains",
    negative_prompt="blurry, ugly, distorted",
    width=1024,
    height=768
)
```

### With Specific LoRA
```python
await generate_image(
    prompt="a beautiful sunset over mountains",
    loras=["ghibliStyle_kontext_byJaneB"],
    width=1024,
    height=768
)
```

## Benefits

1. **Future-Proof**: Works with any ComfyUI workflow structure
2. **No Manual Configuration**: Automatically adapts to different node layouts
3. **Intelligent Defaults**: Smart fallbacks when nodes aren't found
4. **LoRA Management**: Automatic LoRA discovery and application
5. **Error Resilient**: Graceful handling of missing nodes or invalid configurations

## Next Steps

To further enhance the system:
1. **Multi-LoRA Support**: Chain multiple LoRA loaders for complex styles
2. **Image-to-Image**: Add support for img2img workflows
3. **Advanced Sampling**: Support for custom schedulers and samplers
4. **Style Presets**: Pre-configured LoRA combinations for different art styles
