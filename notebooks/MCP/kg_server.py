import argparse
import os
import json
#from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(
    name="Knowledge-Base",
    host="0.0.0.0",
    port=8050,
    stateless_http=True,
)


@mcp.tool()
def get_knowledge_base() -> str:
    """Retrieve the entire knowledge base as a formatted string.

    Returns:
        A formatted string containing all Q&A pairs from the knowledge base.
    """
    try:
        kb_path = os.path.join(os.path.dirname(__file__), "data", "kb.json")
        with open(kb_path, "r") as f:
            kb_data = json.load(f)

        # Format the knowledge base as a string
        kb_text = "Here is the retrieved knowledge base:\n\n"

        if isinstance(kb_data, list):
            for i, item in enumerate(kb_data, 1):
                if isinstance(item, dict):
                    question = item.get("question", "Unknown question")
                    answer = item.get("answer", "Unknown answer")
                else:
                    question = f"Item {i}"
                    answer = str(item)

                kb_text += f"Q{i}: {question}\n"
                kb_text += f"A{i}: {answer}\n\n"
        else:
            kb_text += f"Knowledge base content: {json.dumps(kb_data, indent=2)}\n\n"

        return kb_text
    except FileNotFoundError:
        return "Error: Knowledge base file not found"
    except json.JSONDecodeError:
        return "Error: Invalid JSON in knowledge base file"
    except Exception as e:
        return f"Error: {str(e)}"


# Run the server
if __name__ == "__main__":
        # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run MCP Calculator Server")
    parser.add_argument(
        "-t", "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport method to use (default: stdio)"
    )
    parser.add_argument(
        "-host", "--host",
        default="0.0.0.0",
        help="Host to use (default: 0.0.0.0)"
    )
    parser.add_argument(
        "-port", "--port",
        default=8050,
        help="Port to use (default: 8050)"
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
        mcp.run(transport="http",host=args.host,port=args.port,path="/mcp")
    else:
        raise ValueError(f"Unknown transport: {transport}")