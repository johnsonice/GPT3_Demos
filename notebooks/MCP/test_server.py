from fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="http",path="/mcp")