# Timeout Configuration Guide

## Overview

The Imagyn MCP server now supports configurable timeout values throughout the entire codebase. All timeout values are configured through the `config.json` file and are applied consistently across all server implementations.

## Configuration Parameters

Add these parameters to your `config.json` file:

```json
{
  "http_timeout": 60.0,           // HTTP client timeout in seconds
  "websocket_timeout": 30.0,      // WebSocket message timeout in seconds  
  "default_generation_timeout": 300  // Overall generation timeout in seconds
}
```

## Timeout Types

### 1. HTTP Timeout (`http_timeout`)
- **Purpose**: Controls timeout for HTTP API calls to ComfyUI server
- **Default**: 60.0 seconds
- **Used for**: Connection tests, queuing prompts, downloading images, getting history
- **Recommended for network setups**: 90+ seconds if ComfyUI is on a different machine

### 2. WebSocket Timeout (`websocket_timeout`)
- **Purpose**: Controls timeout for individual WebSocket message receives
- **Default**: 30.0 seconds
- **Used for**: Monitoring generation progress via WebSocket
- **Recommended for slow generations**: 60+ seconds if generation takes >120 seconds

### 3. Generation Timeout (`default_generation_timeout`)
- **Purpose**: Maximum total time allowed for image generation
- **Default**: 300 seconds (5 minutes)
- **Used for**: Overall timeout for complete generation process
- **Recommended for complex generations**: 400+ seconds for high-quality/complex prompts

## Files Updated

### Core Configuration
- `src/imagyn/models.py` - Added timeout fields to ImagynConfig
- `config.json` - Added timeout configuration values

### ComfyUI Client
- `src/imagyn/comfyui_client.py` - Updated to accept and use configurable timeouts

### Server Implementations
- `stdio_mcp_server.py` - Uses config timeouts directly
- `src/imagyn/fastmcp_server.py` - Passes config timeouts to ComfyUIClient
- `src/imagyn/imagyn_server.py` - Passes config timeouts to ComfyUIClient

### Status Reporting
All server implementations now report current timeout configurations in their status responses.

## Backward Compatibility

- All timeout parameters have sensible defaults
- Existing config files without timeout parameters will use default values
- No breaking changes to existing functionality

## Testing Your Configuration

1. Update your `config.json` with appropriate timeout values
2. Restart the MCP server
3. Use the `get_server_status` tool to verify timeout configurations are loaded
4. Test image generation to ensure timeouts work as expected

## Recommended Settings

### Local Setup (ComfyUI on same machine)
```json
{
  "http_timeout": 30.0,
  "websocket_timeout": 15.0,
  "default_generation_timeout": 180
}
```

### Network Setup (ComfyUI on different machine)
```json
{
  "http_timeout": 90.0,
  "websocket_timeout": 60.0,
  "default_generation_timeout": 400
}
```

### High-Performance Setup (Fast GPU, complex generations)
```json
{
  "http_timeout": 60.0,
  "websocket_timeout": 30.0,
  "default_generation_timeout": 600
}
```
