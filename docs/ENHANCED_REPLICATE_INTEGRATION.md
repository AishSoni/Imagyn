# Enhanced Replicate Integration - Model Parameter Intelligence

## Overview

The MCP server now intelligently handles different Replicate model formats and automatically configures parameters based on the model type. Users only need to specify the `model_id` and the system will handle the rest.

## Configuration

### Simple Configuration (Recommended)
```json
{
  "provider": "replicate",
  "output_folder": "output",
  "replicate": {
    "api_key": "your_replicate_api_key_here",
    "model_id": "black-forest-labs/flux-dev"
  }
}
```

## Supported Model Formats

### 1. Black Forest Labs Models (New Format)
**Examples:**
- `black-forest-labs/flux-dev`
- `black-forest-labs/flux-schnell`

**Auto-configured parameters:**
- `go_fast`: `true` (default)
- `guidance`: `3.5` (default)
- `aspect_ratio`: Calculated from width/height or use provided value
- `megapixels`: "1" (standard)
- `num_inference_steps`: `28` (default)
- `num_outputs`: `1`
- `output_format`: "webp" (default)
- `output_quality`: `80` (default)
- `prompt_strength`: `0.8`

### 2. Legacy Models (Version-based Format)
**Examples:**
- `prunaai/flux.1-dev:b0306d92aa025bb747dc74162f3c27d6ed83798e08e5f8977adf3d859d0536a3`

**Auto-configured parameters:**
- `width`: From tool input (default: 1024)
- `height`: From tool input (default: 1024)
- `speed_mode`: From config or default

## Available Tool Parameters

All parameters are optional - the system provides intelligent defaults:

### Core Parameters
- `prompt` (required): Text description for image generation
- `negative_prompt`: Elements to avoid (legacy models only)

### Dimension Parameters
- `width`: Image width in pixels (64-2048)
- `height`: Image height in pixels (64-2048)
- `aspect_ratio`: Aspect ratio (new models) - "1:1", "16:9", "9:16", etc.

### Quality Parameters
- `guidance`: Guidance scale (1-20, default varies by model)
- `num_inference_steps`: Number of steps (1-50, default: 28)
- `go_fast`: Enable fast mode (new models only)

### Output Parameters
- `output_format`: "png", "jpg", "webp" (default: webp)
- `output_quality`: Quality for compressed formats (1-100, default: 80)
- `seed`: Random seed for reproducibility

## Intelligent Parameter Mapping

### Aspect Ratio Auto-Detection
When width/height are provided but no aspect_ratio:
- Square (1:1): width == height
- Landscape: width > height
  - 16:9 if ratio ≥ 1.7
  - 3:2 if ratio < 1.7
- Portrait: height > width
  - 9:16 if ratio ≥ 1.7
  - 2:3 if ratio < 1.7

### Model Type Detection
The system automatically detects model capabilities:
- **Black Forest Labs models**: Use new API parameters (aspect_ratio, go_fast, etc.)
- **Legacy models**: Use traditional parameters (width, height, speed_mode)

## Example Usage

### Basic Generation
```
generate_image with prompt: "A beautiful sunset over mountains"
```
Result: Uses all default parameters optimized for the configured model.

### Advanced Generation
```
generate_image with:
- prompt: "A futuristic city at night"
- aspect_ratio: "16:9"
- guidance: 7.5
- go_fast: true
- output_format: "png"
```

### Legacy Model Support
The system still supports older model formats and will automatically use appropriate parameters.

## Benefits

1. **Simplified Configuration**: Only model_id needed
2. **Automatic Optimization**: Parameters optimized per model type
3. **Backward Compatibility**: Supports both new and legacy models
4. **Intelligent Defaults**: No need to research model-specific parameters
5. **Flexible Override**: Users can still specify custom parameters when needed

## Model Switching

To switch models, simply update the `model_id` in config.json:

```json
{
  "replicate": {
    "api_key": "your_key",
    "model_id": "black-forest-labs/flux-schnell"  // Changed from flux-dev
  }
}
```

The system will automatically adapt to the new model's parameter requirements.
