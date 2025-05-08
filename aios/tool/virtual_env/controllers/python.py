import json
import logging
import random
from typing import Any, Dict, Optional
import time
import requests

from virtual_env.actions import KEYBOARD_KEYS

logger = logging.getLogger("desktopenv.pycontroller")


class PythonController:
    def __init__(self, vm_ip: str,
                 server_port: int,
                 pkgs_prefix: str = "import pyautogui; import time; pyautogui.FAILSAFE = False; {command}"):
        self.vm_ip = vm_ip
        self.http_server = f"http://{vm_ip}:{server_port}"
        self.pkgs_prefix = pkgs_prefix  # fixme: this is a hacky way to execute python commands. fix it and combine it with installation of packages
        self.retry_times = 3
        self.retry_interval = 5

    def get_screenshot(self) -> Optional[bytes]:
        """
        Gets a screenshot from the server. With the cursor. None -> no screenshot or unexpected error.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.get(self.http_server + "/screenshot")
                if response.status_code == 200:
                    logger.info("Got screenshot successfully")
                    return response.content
                else:
                    logger.error("Failed to get screenshot. Status code: %d", response.status_code)
                    logger.info("Retrying to get screenshot.")
            except Exception as e:
                logger.error("An error occurred while trying to get the screenshot: %s", e)
                logger.info("Retrying to get screenshot.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get screenshot.")
        return None

    def get_accessibility_tree(self) -> Optional[str]:
        """
        Gets the accessibility tree from the server. None -> no accessibility tree or unexpected error.
        """

        for _ in range(self.retry_times):
            try:
                response: requests.Response = requests.get(self.http_server + "/accessibility")
                if response.status_code == 200:
                    logger.info("Got accessibility tree successfully")
                    return response.json()["AT"]
                else:
                    logger.error("Failed to get accessibility tree. Status code: %d", response.status_code)
                    logger.info("Retrying to get accessibility tree.")
            except Exception as e:
                logger.error("An error occurred while trying to get the accessibility tree: %s", e)
                logger.info("Retrying to get accessibility tree.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get accessibility tree.")
        return None

    def get_terminal_output(self) -> Optional[str]:
        """
        Gets the terminal output from the server. None -> no terminal output or unexpected error.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.get(self.http_server + "/terminal")
                if response.status_code == 200:
                    logger.info("Got terminal output successfully")
                    return response.json()["output"]
                else:
                    logger.error("Failed to get terminal output. Status code: %d", response.status_code)
                    logger.info("Retrying to get terminal output.")
            except Exception as e:
                logger.error("An error occurred while trying to get the terminal output: %s", e)
                logger.info("Retrying to get terminal output.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get terminal output.")
        return None

    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Gets a file from the server.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/file", data={"file_path": file_path})
                if response.status_code == 200:
                    logger.info("File downloaded successfully")
                    return response.content
                else:
                    logger.error("Failed to get file. Status code: %d", response.status_code)
                    logger.info("Retrying to get file.")
            except Exception as e:
                logger.error("An error occurred while trying to get the file: %s", e)
                logger.info("Retrying to get file.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get file.")
        return None
    
    def reset(self):
        """
        Resets the server.
        """
        command = "echo 'password' | sudo -S systemctl restart gdm"
        payload = json.dumps({"command": command, "shell": True})
        response = requests.post(self.http_server + "/execute", headers={'Content-Type': 'application/json'},
                                         data=payload, timeout=90)
        if response.status_code == 200:
            logger.info("Reset successfully")
        
        else:
            logger.error("Failed to reset. Status code: %d", response.status_code)

    def execute_python_command(self, command: str) -> None:
        """
        Executes a python command on the server.
        It can be used to execute the pyautogui commands, or... any other python command. who knows?
        """
        # command_list = ["python", "-c", self.pkgs_prefix.format(command=command)]
        command_list = ["python", "-c", self.pkgs_prefix.format(command=command)]
        payload = json.dumps({"command": command_list, "shell": False})

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/execute", headers={'Content-Type': 'application/json'},
                                         data=payload, timeout=90)
                if response.status_code == 200:
                    logger.info("Command executed successfully: %s", response.text)
                    return response.json()
                else:
                    logger.error("Failed to execute command. Status code: %d", response.status_code)
                    logger.info("Retrying to execute command.")
            except requests.exceptions.ReadTimeout:
                break
            except Exception as e:
                logger.error("An error occurred while trying to execute the command: %s", e)
                logger.info("Retrying to execute command.")
            time.sleep(self.retry_interval)

        logger.error("Failed to execute command.")
        return None

    def execute_action(self, action: Dict[str, Any]):
        """
        Executes an action on the server computer.
        """
        if action in ['wait', 'fail', 'done']:
            return

        action_type = action["action_type"].lower()
        parameters = action["parameters"] if "parameters" in action else {param: action[param] for param in action if param != 'action_type'}
        move_mode = random.choice(
            ["pyautogui.easeInQuad", "pyautogui.easeOutQuad", "pyautogui.easeInOutQuad", "pyautogui.easeInBounce",
             "pyautogui.easeInElastic"])
        duration = random.uniform(0.5, 1)

        if action_type == "move_to":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.moveTo()")
            elif "x" in parameters and "y" in parameters:
                x = parameters["x"]
                y = parameters["y"]
                self.execute_python_command(f"pyautogui.moveTo({x}, {y}, {duration}, {move_mode})")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "click":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.click()")
            elif "button" in parameters and "x" in parameters and "y" in parameters:
                button = parameters["button"]
                x = parameters["x"]
                y = parameters["y"]
                if "num_clicks" in parameters:
                    num_clicks = parameters["num_clicks"]
                    self.execute_python_command(
                        f"pyautogui.click(button='{button}', x={x}, y={y}, clicks={num_clicks})")
                else:
                    self.execute_python_command(f"pyautogui.click(button='{button}', x={x}, y={y})")
            elif "button" in parameters and "x" not in parameters and "y" not in parameters:
                button = parameters["button"]
                if "num_clicks" in parameters:
                    num_clicks = parameters["num_clicks"]
                    self.execute_python_command(f"pyautogui.click(button='{button}', clicks={num_clicks})")
                else:
                    self.execute_python_command(f"pyautogui.click(button='{button}')")
            elif "button" not in parameters and "x" in parameters and "y" in parameters:
                x = parameters["x"]
                y = parameters["y"]
                if "num_clicks" in parameters:
                    num_clicks = parameters["num_clicks"]
                    self.execute_python_command(f"pyautogui.click(x={x}, y={y}, clicks={num_clicks})")
                else:
                    self.execute_python_command(f"pyautogui.click(x={x}, y={y})")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "mouse_down":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.mouseDown()")
            elif "button" in parameters:
                button = parameters["button"]
                self.execute_python_command(f"pyautogui.mouseDown(button='{button}')")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "mouse_up":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.mouseUp()")
            elif "button" in parameters:
                button = parameters["button"]
                self.execute_python_command(f"pyautogui.mouseUp(button='{button}')")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "right_click":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.rightClick()")
            elif "x" in parameters and "y" in parameters:
                x = parameters["x"]
                y = parameters["y"]
                self.execute_python_command(f"pyautogui.rightClick(x={x}, y={y})")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "double_click":
            if parameters == {} or None:
                self.execute_python_command("pyautogui.doubleClick()")
            elif "x" in parameters and "y" in parameters:
                x = parameters["x"]
                y = parameters["y"]
                self.execute_python_command(f"pyautogui.doubleClick(x={x}, y={y})")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "drag_to":
            if "x" in parameters and "y" in parameters:
                x = parameters["x"]
                y = parameters["y"]
                self.execute_python_command(
                    f"pyautogui.dragTo({x}, {y}, duration=1.0, button='left', mouseDownUp=True)")

        elif action_type == "scroll":
            # todo: check if it is related to the operating system, as https://github.com/TheDuckAI/DuckTrack/blob/main/ducktrack/playback.py pointed out
            if "dx" in parameters and "dy" in parameters:
                dx = parameters["dx"]
                dy = parameters["dy"]
                self.execute_python_command(f"pyautogui.hscroll({dx})")
                self.execute_python_command(f"pyautogui.vscroll({dy})")
            elif "dx" in parameters and "dy" not in parameters:
                dx = parameters["dx"]
                self.execute_python_command(f"pyautogui.hscroll({dx})")
            elif "dx" not in parameters and "dy" in parameters:
                dy = parameters["dy"]
                self.execute_python_command(f"pyautogui.vscroll({dy})")
            else:
                raise Exception(f"Unknown parameters: {parameters}")

        elif action_type == "typing":
            if "text" not in parameters:
                raise Exception(f"Unknown parameters: {parameters}")
            # deal with special ' and \ characters
            # text = parameters["text"].replace("\\", "\\\\").replace("'", "\\'")
            # self.execute_python_command(f"pyautogui.typewrite('{text}')")
            text = parameters["text"]
            self.execute_python_command("pyautogui.typewrite({:})".format(repr(text)))

        elif action_type == "press":
            if "key" not in parameters:
                raise Exception(f"Unknown parameters: {parameters}")
            key = parameters["key"]
            if key.lower() not in KEYBOARD_KEYS:
                raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
            self.execute_python_command(f"pyautogui.press('{key}')")

        elif action_type == "key_down":
            if "key" not in parameters:
                raise Exception(f"Unknown parameters: {parameters}")
            key = parameters["key"]
            if key.lower() not in KEYBOARD_KEYS:
                raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
            self.execute_python_command(f"pyautogui.keyDown('{key}')")

        elif action_type == "key_up":
            if "key" not in parameters:
                raise Exception(f"Unknown parameters: {parameters}")
            key = parameters["key"]
            if key.lower() not in KEYBOARD_KEYS:
                raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
            self.execute_python_command(f"pyautogui.keyUp('{key}')")

        elif action_type == "hotkey":
            if "keys" not in parameters:
                raise Exception(f"Unknown parameters: {parameters}")
            keys = parameters["keys"]
            if not isinstance(keys, list):
                raise Exception("Keys must be a list of keys")
            for key in keys:
                if key.lower() not in KEYBOARD_KEYS:
                    raise Exception(f"Key must be one of {KEYBOARD_KEYS}")

            keys_para_rep = "', '".join(keys)
            self.execute_python_command(f"pyautogui.hotkey('{keys_para_rep}')")

        elif action_type in ['wait', 'fail', 'done']:
            pass

        else:
            raise Exception(f"Unknown action type: {action_type}")

    # Record video
    def start_recording(self):
        """
        Starts recording the screen.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/start_recording")
                if response.status_code == 200:
                    logger.info("Recording started successfully")
                    return
                else:
                    logger.error("Failed to start recording. Status code: %d", response.status_code)
                    logger.info("Retrying to start recording.")
            except Exception as e:
                logger.error("An error occurred while trying to start recording: %s", e)
                logger.info("Retrying to start recording.")
            time.sleep(self.retry_interval)

        logger.error("Failed to start recording.")

    def end_recording(self, dest: str):
        """
        Ends recording the screen.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/end_recording")
                if response.status_code == 200:
                    logger.info("Recording stopped successfully")
                    with open(dest, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return
                else:
                    logger.error("Failed to stop recording. Status code: %d", response.status_code)
                    logger.info("Retrying to stop recording.")
            except Exception as e:
                logger.error("An error occurred while trying to stop recording: %s", e)
                logger.info("Retrying to stop recording.")
            time.sleep(self.retry_interval)

        logger.error("Failed to stop recording.")

    # Additional info
    def get_vm_platform(self):
        """
        Gets the size of the vm screen.
        """
        return self.execute_python_command("import platform; print(platform.system())")['output'].strip()

    def get_vm_screen_size(self):
        """
        Gets the size of the vm screen.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/screen_size")
                if response.status_code == 200:
                    logger.info("Got screen size successfully")
                    return response.json()
                else:
                    logger.error("Failed to get screen size. Status code: %d", response.status_code)
                    logger.info("Retrying to get screen size.")
            except Exception as e:
                logger.error("An error occurred while trying to get the screen size: %s", e)
                logger.info("Retrying to get screen size.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get screen size.")
        return None

    def get_vm_window_size(self, app_class_name: str):
        """
        Gets the size of the vm app window.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/window_size", data={"app_class_name": app_class_name})
                if response.status_code == 200:
                    logger.info("Got window size successfully")
                    return response.json()
                else:
                    logger.error("Failed to get window size. Status code: %d", response.status_code)
                    logger.info("Retrying to get window size.")
            except Exception as e:
                logger.error("An error occurred while trying to get the window size: %s", e)
                logger.info("Retrying to get window size.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get window size.")
        return None

    def get_vm_wallpaper(self):
        """
        Gets the wallpaper of the vm.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/wallpaper")
                if response.status_code == 200:
                    logger.info("Got wallpaper successfully")
                    return response.content
                else:
                    logger.error("Failed to get wallpaper. Status code: %d", response.status_code)
                    logger.info("Retrying to get wallpaper.")
            except Exception as e:
                logger.error("An error occurred while trying to get the wallpaper: %s", e)
                logger.info("Retrying to get wallpaper.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get wallpaper.")
        return None

    def get_vm_desktop_path(self) -> Optional[str]:
        """
        Gets the desktop path of the vm.
        """

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/desktop_path")
                if response.status_code == 200:
                    logger.info("Got desktop path successfully")
                    return response.json()["desktop_path"]
                else:
                    logger.error("Failed to get desktop path. Status code: %d", response.status_code)
                    logger.info("Retrying to get desktop path.")
            except Exception as e:
                logger.error("An error occurred while trying to get the desktop path: %s", e)
                logger.info("Retrying to get desktop path.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get desktop path.")
        return None

    def get_vm_directory_tree(self, path) -> Optional[Dict[str, Any]]:
        """
        Gets the directory tree of the vm.
        """
        payload = json.dumps({"path": path})

        for _ in range(self.retry_times):
            try:
                response = requests.post(self.http_server + "/list_directory", headers={'Content-Type': 'application/json'}, data=payload)
                if response.status_code == 200:
                    logger.info("Got directory tree successfully")
                    return response.json()["directory_tree"]
                else:
                    logger.error("Failed to get directory tree. Status code: %d", response.status_code)
                    logger.info("Retrying to get directory tree.")
            except Exception as e:
                logger.error("An error occurred while trying to get directory tree: %s", e)
                logger.info("Retrying to get directory tree.")
            time.sleep(self.retry_interval)

        logger.error("Failed to get directory tree.")
        return None
