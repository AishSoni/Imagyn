"""
Simple test MCP server to verify ChatMCP connectivity
"""

from mcp.server.fastmcp import FastMCP

# Create a simple test server
mcp = FastMCP("Test Server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@mcp.tool()
def test_connection() -> dict:
    """Test the connection"""
    return {
        "status": "connected",
        "message": "MCP server is working correctly"
    }

if __name__ == "__main__":
    mcp.run()
