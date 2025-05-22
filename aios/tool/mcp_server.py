# from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP
import subprocess, json, os, shlex
import time

mcp = FastMCP("linux-mcp")

from typing import List, Dict, Any

file_dir = os.path.dirname(os.path.abspath(__file__))

path_to_vm = os.path.join(file_dir, "vmware_vm_data", "Ubuntu0", "Ubuntu0.vmx")

from virtual_env.desktop_env import DesktopEnv

virtual_env = DesktopEnv(path_to_vm=path_to_vm)

# ---------- MCP TOOLS ----------
@mcp.tool(description="Move mouse to absolute X/Y coordinates (pixels)")
async def move_mouse(x: int, y: int) -> str:
    ACTION_TYPE = "move_to"
    parameters = {"x": x, "y": y}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Click the mouse at the current position")
async def click(x: int = None, y: int = None, num_clicks: int = None) -> str:
    ACTION_TYPE = "click"
    parameters = {}
    if x is not None and y is not None:
        parameters["x"] = x
        parameters["y"] = y
    if num_clicks is not None:
        parameters["num_clicks"] = num_clicks
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Right click the mouse at the current position")
async def right_click(x: int = None, y: int = None) -> str:
    ACTION_TYPE = "right_click"
    parameters = {"x": x, "y": y} if x is not None and y is not None else {}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)


@mcp.tool(description="Type text at the current cursor position")
async def typing(text: str) -> str:
    ACTION_TYPE = "typing"
    parameters = {"text": text}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Double click the mouse at the current position")
async def double_click(x: int = None, y: int = None) -> str:
    ACTION_TYPE = "double_click"
    parameters = {"x": x, "y": y} if x is not None and y is not None else {}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Drag the mouse to the absolute X/Y coordinates (pixels)")
async def drag_to(x: int, y: int) -> str:
    ACTION_TYPE = "drag_to"
    parameters = {"x": x, "y": y}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Take a screenshot of the current screen")
async def screenshot() -> str:
    return virtual_env.controller.get_screenshot()

@mcp.tool(description="Reset the VM")
async def reset_vm(task_config: Dict[str, Any]) -> str:
    return await virtual_env.reset(task_config)

@mcp.tool(description="Get the accessibility tree of the current screen")
async def get_accessibility_tree() -> str:
    return virtual_env.controller.get_accessibility_tree()

@mcp.tool(description="Evaluate the current task")
async def evaluate(action_history: List[Dict[str, Any]]) -> str:
    return await virtual_env.evaluate(action_history)

@mcp.tool(description="Scroll the mouse wheel up or down")
async def scroll(dx: int, dy: int) -> str:
    ACTION_TYPE = "scroll"
    parameters = {"dx": dx, "dy": dy}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Press a key")
async def press(key: str) -> str:
    ACTION_TYPE = "press"
    parameters = {"key": key}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Key up")
async def release(key: str) -> str:
    ACTION_TYPE = "release"
    parameters = {"key": key}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Hotkey the current window")
async def hotkey(keys: List[str]) -> str:
    ACTION_TYPE = "hotkey"
    parameters = {"keys": keys}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Wait for a few seconds")
async def wait(seconds: int = None) -> str:
    # ACTION_TYPE = "wait"
    # if seconds is None:
    #     seconds = 1
    time.sleep(seconds)
    return

@mcp.tool(description="Launch an application")
async def launch(app_name: str) -> str:
    ACTION_TYPE = "launch"
    parameters = {"app_name": app_name}
    action = {"action_type": ACTION_TYPE, "parameters": parameters}
    return virtual_env.controller.execute_action(action)

@mcp.tool(description="Start recording the screen")
async def start_recording() -> str:
    return virtual_env.controller.start_recording()

@mcp.tool(description="Stop recording the screen")
async def stop_recording(file_name: str) -> str:
    return virtual_env.controller.end_recording(file_name)

if __name__ == "__main__":
    mcp.run(transport="stdio")   # 1-line launch as required by the spec :contentReference[oaicite:4]{index=4}
