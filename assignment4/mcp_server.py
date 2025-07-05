from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Create MCP server instance
mcp = FastMCP("String Reverser")

@mcp.tool()
async def reverse_string(text: str) -> dict:
    """Reverse a given string"""
    return {
        "content": [
            TextContent(
                type="text",
                text=text[::-1] 
            )
        ]
    }

if __name__ == "__main__":
    print("Starting MCP String Reverser server...")
    mcp.run() 