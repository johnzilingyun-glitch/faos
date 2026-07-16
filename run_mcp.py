import os
import argparse
from faos.api.mcp_server import mcp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FAOS MCP Server")
    parser.add_argument("--transport", type=str, choices=["stdio", "sse"], default="stdio", 
                        help="Transport protocol (stdio or sse)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=8002, help="Port for SSE transport")
    
    args = parser.parse_args()
    
    # We must enforce Mock for local testing if API keys are missing
    if "FAOS_LLM_PROVIDER" not in os.environ:
        os.environ["FAOS_LLM_PROVIDER"] = "mock"
    
    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        mcp.run("sse", host=args.host, port=args.port)
