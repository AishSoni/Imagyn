#!/usr/bin/env python3
"""
Minimal MCP server test to debug tool registration
"""

import asyncio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio


class MinimalMCPServer:
    def __init__(self):
        self.server = Server("test-server")
        self._setup_tools()
    
    def _setup_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="test_tool",
                    description="A simple test tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Test message"
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            if name == "test_tool":
                message = arguments.get("message", "Hello")
                return [types.TextContent(
                    type="text",
                    text=f"Test tool called with message: {message}"
                )]
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def start(self):
        print("Starting minimal MCP server...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="test-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=types.NotificationOptions(),
                        experimental_capabilities=None,
                    ),
                ),
            )


if __name__ == "__main__":
    server = MinimalMCPServer()
    asyncio.run(server.start())
