"""
Imagyn MCP Server - Main entry point
"""

import asyncio
from imagyn.mcp import MCPServer


def main():
    asyncio.run(MCPServer().start())

if __name__ == "__main__":
    main()
