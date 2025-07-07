#%%
##from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP
from dotenv import load_dotenv
import argparse

load_dotenv("../../.env")

# Create an MCP server
mcp = FastMCP(
    name="Calculator",
    host="0.0.0.0",         # only used for SSE transport (localhost)
    port=8050,              # only used for SSE transport (set this to any port)
    stateless_http=True,
)

# Add a simple calculator tool ; this can be any function that can be called by the MCP server
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


# Run the server
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run MCP Calculator Server")
    parser.add_argument(
        "-t", "--transport",
        choices=["stdio", "sse", "http"],
        default="sse",
        help="Transport method to use (default: stdio)"
    )
    
    args = parser.parse_args()
    transport = args.transport
    
    if transport == "stdio":
        print("Running server with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        print("Running server with SSE transport")
        mcp.run(transport="sse")
    elif transport == "http":
        print("Running server with Streamable HTTP transport")
        mcp.run(transport="http",path="/mcp")
    else:
        raise ValueError(f"Unknown transport: {transport}")
