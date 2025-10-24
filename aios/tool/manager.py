import importlib
import subprocess
import os # Added for path manipulation
import signal # Added to send signals to subprocess

# from cerebrum.llm.communication import Response

from aios.config.config_manager import config

from cerebrum.tool.apis import ToolResponse

from cerebrum.interface import AutoTool

from threading import Lock

class ToolManager:
    def __init__(
        self,
        log_mode: str = "console",
    ):
        self.log_mode = log_mode
        self.tool_conflict_map = {}
        self.tool_conflict_map_lock = Lock()
        self.mcp_server_process = None # To store the mcp_server subprocess
        self._start_mcp_server() # Start mcp_server on initialization
        
    def _start_mcp_server(self):
        """Starts the mcp_server.py script as a background subprocess."""
        if self.mcp_server_process is None or self.mcp_server_process.poll() is not None:
            try:
                # Assuming mcp_server.py is in the same directory as manager.py
                mcp_server_script_path = config.get_mcp_server_script_path()
                if not os.path.exists(mcp_server_script_path):
                    print(f"Error: mcp_server.py not found at {mcp_server_script_path}")
                    return

                # Start the server
                # We use Popen for non-blocking execution and to manage the process
                self.mcp_server_process = subprocess.Popen(
                    ["python", mcp_server_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                print(f"MCP Server started with PID: {self.mcp_server_process.pid}")
                # TODO: Add a mechanism to check if the server started successfully (e.g., by checking its output or a health endpoint if it has one)
            except Exception as e:
                print(f"Failed to start MCP Server: {e}")
                self.mcp_server_process = None
        else:
            print("MCP Server is already running.")

    def _stop_mcp_server(self):
        """Stops the mcp_server subprocess if it is running."""
        if self.mcp_server_process and self.mcp_server_process.poll() is None:
            print(f"Stopping MCP Server with PID: {self.mcp_server_process.pid}...")
            try:
                # Terminate the process gracefully
                self.mcp_server_process.terminate()
                # Wait for a bit for the process to terminate
                self.mcp_server_process.wait(timeout=5)
                print("MCP Server terminated.")
            except subprocess.TimeoutExpired:
                print("MCP Server did not terminate in time, killing it.")
                self.mcp_server_process.kill()
                self.mcp_server_process.wait()
                print("MCP Server killed.")
            except Exception as e:
                print(f"Error stopping MCP Server: {e}")
            finally:
                self.mcp_server_process = None
        else:
            print("MCP Server is not running or already stopped.")
            
    def cleanup(self):
        """Cleanup resources, including stopping the mcp_server."""
        print("Cleaning up ToolManager...")
        self._stop_mcp_server()
        
    def address_request(self, syscall) -> None:
        tool_calls = syscall.query.tool_calls

        if tool_calls == None or len(tool_calls) == 0:
            return ToolResponse(
                response_message=f"There is no tool to call",
                finished=False
            )
        # breakpoint()
        try:
            for tool_call in tool_calls:
                tool_org_and_name, tool_params = (
                    tool_call["name"],
                    tool_call["parameters"],
                )
                # org, tool_name = tool_org_and_name.split("/")
                with self.tool_conflict_map_lock:
                    if tool_org_and_name not in self.tool_conflict_map.keys():
                        self.tool_conflict_map[tool_org_and_name] = 1
                        tool = self.load_tool_instance(tool_org_and_name)

                        # tool = tool_class()
                        tool_result = tool.run(params=tool_params)

                        self.tool_conflict_map.pop(tool_org_and_name)
                        
                        return ToolResponse(
                            response_message=tool_result,
                            finished=True
                        )
                    
        except Exception as e:
            return ToolResponse(
                response_message=f"Tool calling error: {e}",
                finished=False
            )

    def load_tool_instance(self, tool_org_and_name):
        tool_instance = AutoTool.from_preloaded(tool_org_and_name)
        return tool_instance
