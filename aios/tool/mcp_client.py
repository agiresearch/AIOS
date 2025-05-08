# local_test_agent.py
# connect.py  – import and call connect_to_server() instead of your old snippet
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any, Optional, Literal, Tuple, Union
import asyncio


import logging
logger = logging.getLogger("desktopenv.mcp_client")

class MCPClient:
    def __init__(self) -> None:
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self.session: Optional[ClientSession] = None

    async def connect(self, server_script_path: str):
        # Decide which interpreter to use from the file extension
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"

        # 1️⃣  Describe how to start the server (stdio transport)
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None,           # inherit current env; customise if needed
        )

        # 2️⃣  Open the bidirectional stdio pipes and push them on the stack
        stdio_reader, stdio_writer = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        # 3️⃣  Create an MCP ClientSession on those pipes
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio_reader, stdio_writer)
        )

        # 4️⃣  Do the protocol handshake (MUST be called once) :contentReference[oaicite:1]{index=1}
        await self.session.initialize()

    async def get_tools(self):
        # 5️⃣  List tools so the user / calling code can see what’s available
        resp = await self.session.list_tools()
        # tool_names = [t.name for t in resp.tools]
        # # print("✅  Connected – server exposes tools:", tool_names)
        # return tool_names
        return resp.tools
    
    async def get_tool_schemas(self):
        openai_tool_schemas = []
        tools = await self.get_tools()
        for tool in tools:
            schema = tool.inputSchema
            if "$schema" in schema:
                schema.pop("$schema")
            openai_tool_schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": schema,
                    },
                }
            )
        return openai_tool_schemas
    
    async def call_tool(self, tool_name, args):
        return await self.session.call_tool(tool_name, args)

    async def close(self):
        await self.exit_stack.aclose()

