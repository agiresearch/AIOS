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

KEYBOARD_KEYS = ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', 'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace', 'browserback', 'browserfavorites', 'browserforward', 'browserhome', 'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear', 'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete', 'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20', 'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja', 'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail', 'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack', 'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn', 'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn', 'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator', 'shift', 'shiftleft', 'shiftright', 'sleep', 'stop', 'subtract', 'tab', 'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen', 'command', 'option', 'optionleft', 'optionright']

"""
Executes an action on the server computer.
"""


# ---------- MCP TOOLS ----------
@mcp.tool(description="Move mouse to absolute X/Y coordinates (pixels)")
async def move_mouse(x: int, y: int) -> str:
    command = f"pyautogui.moveTo({x}, {y})"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Click the mouse at the current position")
async def click(x: int = None, y: int = None, button: str = "left", num_clicks: int = 1) -> str:
    if button != "left":
        command = f"pyautogui.click(button='{button}', x={x}, y={y}, clicks={num_clicks})"
    else:
        command = f"pyautogui.click(x={x}, y={y}, clicks={num_clicks})"
    
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Mouse down at current position")
async def mouse_down(button: str = "left") -> str:
    command = f"pyautogui.mouseDown(button='{button}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Mouse up at current position")
async def mouse_up(button: str = "left") -> str:
    command = f"pyautogui.mouseUp(button='{button}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Type text at the current cursor position")
async def typing(text: str, overwrite: bool = False, enter: bool = False) -> str:
    """Type text into a specific element
    Args:
        element_description:str, a detailed description of which element to enter text in. This description should be at least a full sentence.
        text:str, the text to type
        overwrite:bool, Assign it to True if the text should overwrite the existing text, otherwise assign it to False. Using this argument clears all text in an element.
        enter:bool, Assign it to True if the enter key should be pressed after typing the text, otherwise assign it to False.
    """
    command = "import pyautogui; "

    if overwrite:
        command += (
            f"pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace'); "
        )

    command += f"pyautogui.write({repr(text)}); "

    if enter:
        command += "pyautogui.press('enter'); "
    
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Switch to a different application that is already open")
async def switch_applications(app_code: str) -> str:
    """Switch to a different application that is already open
    Args:
        app_code:str the code name of the application to switch to from the provided list of open applications
    """
    UBUNTU_APP_SETUP = f"""import subprocess;
import difflib;
import pyautogui;
pyautogui.press('escape');
time.sleep(0.5);
output = subprocess.check_output(['wmctrl', '-lx']);
output = output.decode('utf-8').splitlines();
window_titles = [line.split(None, 4)[2] for line in output];
closest_matches = difflib.get_close_matches('APP_NAME', window_titles, n=1, cutoff=0.1);
if closest_matches:
    closest_match = closest_matches[0];
    for line in output:
        if closest_match in line:
            window_id = line.split()[0]
            break;
subprocess.run(['wmctrl', '-ia', window_id])
subprocess.run(['wmctrl', '-ir', window_id, '-b', 'add,maximized_vert,maximized_horz'])
"""
    command = UBUNTU_APP_SETUP.replace("APP_NAME", app_code)
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Drag from the starting description to the ending description")
async def drag_and_drop(x1: int, y1: int, x2: int, y2: int, hold_keys: List = []) -> str:
    """Drag from the starting description to the ending description
    Args:
        starting_description:str, a very detailed description of where to start the drag action. This description should be at least a full sentence.
        ending_description:str, a very detailed description of where to end the drag action. This description should be at least a full sentence.
        hold_keys:List list of keys to hold while dragging
    """
    command = "import pyautogui; "

    command += f"pyautogui.moveTo({x1}, {y1}); "
    for k in hold_keys:
        command += f"pyautogui.keyDown({repr(k)}); "
    command += f"pyautogui.dragTo({x2}, {y2}, duration=1.); pyautogui.mouseUp(); "
    for k in hold_keys:
        command += f"pyautogui.keyUp({repr(k)}); "

    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Scroll the element in the specified direction")
async def scroll(x:int, y: int, clicks: int, shift: bool = False) -> str:
    """Scroll the element in the specified direction
    Args:
        element_description:str, a very detailed description of which element to enter scroll in. This description should be at least a full sentence.
        clicks:int, the number of clicks to scroll can be positive (up) or negative (down).
        shift:bool, whether to use shift+scroll for horizontal scrolling
    """

    if shift:
        command = f"import pyautogui; import time; pyautogui.moveTo({x}, {y}); time.sleep(0.5); pyautogui.hscroll({clicks})"
    else:
        command = f"import pyautogui; import time; pyautogui.moveTo({x}, {y}); time.sleep(0.5); pyautogui.vscroll({clicks})"
    
    return virtual_env.controller.execute_command(command)

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

@mcp.tool(description="Press a key")
async def press(key: str) -> str:
    if key.lower() not in KEYBOARD_KEYS:
        raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
    command = f"pyautogui.press('{key}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Key down")
async def key_down(key: str) -> str:
    if key.lower() not in KEYBOARD_KEYS:
        raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
    command = f"pyautogui.keyDown('{key}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Key up")
async def key_up(key: str) -> str:
    if key.lower() not in KEYBOARD_KEYS:
        raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
    command = f"pyautogui.keyUp('{key}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Hotkey combination")
async def hotkey(keys: List[str]) -> str:
    for key in keys:
        if key.lower() not in KEYBOARD_KEYS:
            raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
    
    keys_para_rep = "', '".join(keys)
    command = f"pyautogui.hotkey('{keys_para_rep}')"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Hold a list of keys and press a list of keys")
async def hold_and_press(hold_keys: List[str], press_keys: List[str]) -> str:
    """Hold a list of keys and press a list of keys
    Args:
        hold_keys:List, list of keys to hold
        press_keys:List, list of keys to press in a sequence
    """

    press_keys_str = "[" + ", ".join([f"'{key}'" for key in press_keys]) + "]"
    command = "import pyautogui; "
    for k in hold_keys:
        command += f"pyautogui.keyDown({repr(k)}); "
    command += f"pyautogui.press({press_keys_str}); "
    for k in hold_keys:
        command += f"pyautogui.keyUp({repr(k)}); "

    return command

@mcp.tool(description="Wait for a few seconds")
async def wait(seconds: int = 1) -> str:
    time.sleep(seconds)
    return f"Waited for {seconds} seconds"

@mcp.tool(description="Open an application or file")
async def open(app_or_filename: str) -> str:
    """Open any application or file with name app_or_filename. Use this action to open applications or files on the desktop, do not open manually.
    Args:
        app_or_filename:str, the name of the application or filename to open
    """
    command = f"import pyautogui; pyautogui.hotkey('win'); time.sleep(0.5); pyautogui.write({repr(app_or_filename)}); time.sleep(1.0); pyautogui.hotkey('enter'); time.sleep(0.5)"
    return virtual_env.controller.execute_command(command)

@mcp.tool(description="Start recording the screen")
async def start_recording() -> str:
    return virtual_env.controller.start_recording()

@mcp.tool(description="Stop recording the screen")
async def stop_recording(file_name: str) -> str:
    return virtual_env.controller.end_recording(file_name)

if __name__ == "__main__":
    mcp.run(transport="stdio")   # 1-line launch as required by the spec :contentReference[oaicite:4]{index=4}
