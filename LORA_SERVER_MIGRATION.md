# LoRA Server Query Migration

## Overview

The Imagyn MCP server has been updated to query LoRA models directly from the ComfyUI server instead of scanning a local directory. This change allows the MCP server to work with remote ComfyUI instances and automatically discover all LoRAs available on the ComfyUI server.

## Changes Made

### 1. ComfyUI Client Updates (`src/imagyn/comfyui_client.py`)

- **New Method**: `_get_available_loras_from_server()` - Queries LoRAs via ComfyUI's `/object_info` API endpoint
- **Updated Method**: `_apply_loras_to_workflow()` - Now async and validates LoRAs against server availability
- **Updated Method**: `generate_image()` - Removed `lora_folder` parameter, made LoRA application async
- **Updated Method**: `get_available_loras()` - Now queries server instead of scanning local folder

### 2. MCP Server Updates (`src/imagyn/imagyn_server.py`)

- **Updated**: `_handle_list_loras()` - Now uses server-based LoRA querying with connection validation
- **Updated**: `_handle_generate_image()` and `_handle_edit_image()` - Added `enable_loras` parameter
- **Updated**: `_handle_get_status()` - Status now indicates LoRAs are queried from server
- **Updated**: `start()` - Removed local LoRA folder validation

### 3. Configuration Updates (`src/imagyn/models.py`)

- **Updated**: `ImagynConfig.lora_folder_path` - Now optional (backward compatible)
- **Added**: Deprecation note indicating LoRAs are queried from ComfyUI server

## Benefits

1. **Remote Compatibility**: Works with ComfyUI servers on different machines
2. **Automatic Discovery**: Automatically finds all LoRAs available on the ComfyUI server
3. **No Local Dependencies**: No need to maintain local LoRA folder paths
4. **Real-time Updates**: Always reflects the current state of LoRAs on the server
5. **Better Validation**: Validates LoRA availability before attempting to use them

## API Changes

### ComfyUI Client

The ComfyUI `/object_info` endpoint provides information about all available nodes and their inputs. For LoRA models, the structure looks like:

```json
{
  "LoraLoader": {
    "input": {
      "required": {
        "lora_name": [["lora1.safetensors", "lora2.safetensors", ...], {...}]
      }
    }
  }
}
```

### LoRA Matching Logic

The system now uses intelligent LoRA matching:

1. **Exact Match**: Direct filename match
2. **Extension Addition**: Adds `.safetensors` extension if missing
3. **Partial Match**: Searches for partial name matches
4. **Fallback**: Uses first available LoRA if no match found

## Backward Compatibility

- Existing `config.json` files continue to work
- The `lora_folder_path` field is now optional and ignored
- All existing MCP tool interfaces remain unchanged

## Testing

Use the provided test script to validate the changes:

```bash
python test_lora_server_query.py
```

This script will:
1. Test connection to ComfyUI server
2. Query available LoRAs from the server
3. Display the results

## Configuration

No configuration changes are required. The existing `config.json` can remain as-is:

```json
{
  "comfyui_url": "http://localhost:8188",
  "workflow_file": "workflows/fluxkrea.json",
  "enable_loras": true,
  "lora_folder_path": "models/loras/",  // Now optional/ignored
  "output_folder": "output"
}
```

## Error Handling

The system includes robust error handling:

- **Connection Failures**: Clear error messages when ComfyUI server is unreachable
- **No LoRAs Found**: Graceful handling when no LoRAs are available
- **Invalid LoRAs**: Automatic fallback to available LoRAs when requested LoRA doesn't exist

## Migration Notes

For users with custom implementations:

1. The `lora_folder` parameter has been removed from `generate_image()`
2. LoRA validation now happens asynchronously during workflow application
3. The `get_available_loras()` method no longer requires a folder path parameter

This migration ensures the Imagyn MCP server can work seamlessly with any ComfyUI installation, whether local or remote, and automatically adapts to the available LoRA models on the server.
