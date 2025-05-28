import json
import logging
import os
import os.path
import platform
import shutil
import sqlite3
import tempfile
import time
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from typing import Dict, List

import requests
from playwright.sync_api import sync_playwright, TimeoutError
from playwright.async_api import async_playwright
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile, GoogleDriveFileList
from requests_toolbelt.multipart.encoder import MultipartEncoder

from virtual_env.controllers.python import PythonController
from virtual_env.evaluators.metrics.utils import compare_urls

logger = logging.getLogger("desktopenv.setup")

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class SetupController:
    def __init__(self, vm_ip: str, server_port: int = 5000, chromium_port: int = 9222, vlc_port: int = 8080, cache_dir: str = "cache"):
        self.vm_ip: str = vm_ip
        self.server_port: int = server_port
        self.chromium_port: int = chromium_port
        self.vlc_port: int = vlc_port
        self.http_server: str = f"http://{vm_ip}:{server_port}"
        self.http_server_setup_root: str = f"http://{vm_ip}:{server_port}/setup"
        self.cache_dir: str = cache_dir

    def reset_cache_dir(self, cache_dir: str):
        self.cache_dir = cache_dir

    async def setup(self, config: List[Dict[str, Any]]):
        """
        Args:
            config (List[Dict[str, Any]]): list of dict like {str: Any}. each
              config dict has the structure like
                {
                    "type": str, corresponding to the `_{:}_setup` methods of
                      this class
                    "parameters": dick like {str, Any} providing the keyword
                      parameters
                }
        """

        for cfg in config:
            config_type: str = cfg["type"]
            parameters: Dict[str, Any] = cfg["parameters"]

            # Assumes all the setup the functions should follow this name
            # protocol
            
            logger.info("SETUP: %s(%s)", config_type, str(parameters))
            setup_function: str = "_{:}_setup".format(config_type)
            assert hasattr(self, setup_function), f'Setup controller cannot find init function {setup_function}'
            await getattr(self, setup_function)(**parameters)

            logger.info("SETUP: %s(%s)", setup_function, str(parameters))

    async def _download_setup(self, files: List[Dict[str, str]]):
        """
        Args:
            files (List[Dict[str, str]]): files to download. lisf of dict like
              {
                "url": str, the url to download
                "path": str, the path on the VM to store the downloaded file
              }
        """

        # if not config:
        # return
        # if not 'download' in config:
        # return
        # for url, path in config['download']:
        for f in files:
            url: str = f["url"]
            path: str = f["path"]
            cache_path: str = os.path.join(self.cache_dir, "{:}_{:}".format(
                uuid.uuid5(uuid.NAMESPACE_URL, url),
                os.path.basename(path)))
            if not url or not path:
                raise Exception(f"Setup Download - Invalid URL ({url}) or path ({path}).")

            if not os.path.exists(cache_path):
                max_retries = 3
                downloaded = False
                e = None
                for i in range(max_retries):
                    try:
                        response = requests.get(url, stream=True)
                        response.raise_for_status()

                        with open(cache_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        logger.info("File downloaded successfully")
                        downloaded = True
                        break

                    except requests.RequestException as e:
                        logger.error(
                            f"Failed to download {url} caused by {e}. Retrying... ({max_retries - i - 1} attempts left)")
                if not downloaded:
                    raise requests.RequestException(f"Failed to download {url}. No retries left. Error: {e}")

            form = MultipartEncoder({
                "file_path": path,
                "file_data": (os.path.basename(path), open(cache_path, "rb"))
            })
            headers = {"Content-Type": form.content_type}
            logger.debug(form.content_type)

            # send request to server to upload file
            try:
                logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
                response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
                if response.status_code == 200:
                    logger.info("Command executed successfully: %s", response.text)
                else:
                    logger.error("Failed to upload file. Status code: %s", response.text)
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)

    async def _upload_file_setup(self, files: List[Dict[str, str]]):
        """
        Args:
            files (List[Dict[str, str]]): files to download. lisf of dict like
              {
                "local_path": str, the local path to the file to upload
                "path": str, the path on the VM to store the downloaded file
              }
        """
        for f in files:
            local_path: str = f["local_path"]
            path: str = f["path"]

            if not os.path.exists(local_path):
                logger.error(f"Setup Upload - Invalid local path ({local_path}).")
                return

            form = MultipartEncoder({
                "file_path": path,
                "file_data": (os.path.basename(path), open(local_path, "rb"))
            })
            headers = {"Content-Type": form.content_type}
            logger.debug(form.content_type)

            # send request to server to upload file
            try:
                logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
                response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
                if response.status_code == 200:
                    logger.info("Command executed successfully: %s", response.text)
                else:
                    logger.error("Failed to upload file. Status code: %s", response.text)
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)

    async def _change_wallpaper_setup(self, path: str):
        # if not config:
        # return
        # if not 'wallpaper' in config:
        # return

        # path = config['wallpaper']
        if not path:
            raise Exception(f"Setup Wallpaper - Invalid path ({path}).")

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to change wallpaper
        try:
            response = requests.post(self.http_server + "/setup" + "/change_wallpaper", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to change wallpaper. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    async def _tidy_desktop_setup(self, **config):
        raise NotImplementedError()

    async def _open_setup(self, path: str):
        # if not config:
        # return
        # if not 'open' in config:
        # return
        # for path in config['open']:
        if not path:
            raise Exception(f"Setup Open - Invalid path ({path}).")

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/open_file", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to open file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    async def _launch_setup(self, command: Union[str, List[str]], shell: bool = False):
        if not command:
            raise Exception("Empty command to launch.")

        if not shell and isinstance(command, str) and len(command.split()) > 1:
            logger.warning("Command should be a list of strings. Now it is a string. Will split it by space.")
            command = command.split()

        payload = json.dumps({"command": command, "shell": shell})
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.http_server + "/setup" + "/launch", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to launch application. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    async def _execute_setup(
            self,
            command: List[str],
            stdout: str = "",
            stderr: str = "",
            shell: bool = False,
            until: Optional[Dict[str, Any]] = None
    ):
        if not command:
            raise Exception("Empty command to launch.")

        until: Dict[str, Any] = until or {}
        terminates: bool = False
        nb_failings = 0

        payload = json.dumps({"command": command, "shell": shell})
        headers = {"Content-Type": "application/json"}

        while not terminates:
            try:
                response = requests.post(self.http_server + "/setup" + "/execute", headers=headers, data=payload)
                if response.status_code == 200:
                    results: Dict[str, str] = response.json()
                    if stdout:
                        with open(os.path.join(self.cache_dir, stdout), "w") as f:
                            f.write(results["output"])
                    if stderr:
                        with open(os.path.join(self.cache_dir, stderr), "w") as f:
                            f.write(results["error"])
                    logger.info("Command executed successfully: %s -> %s"
                                , " ".join(command) if isinstance(command, list) else command
                                , response.text
                                )
                else:
                    logger.error("Failed to launch application. Status code: %s", response.text)
                    results = None
                    nb_failings += 1
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)
                traceback.print_exc()

                results = None
                nb_failings += 1

            if len(until) == 0:
                terminates = True
            elif results is not None:
                terminates = "returncode" in until and results["returncode"] == until["returncode"] \
                             or "stdout" in until and until["stdout"] in results["output"] \
                             or "stderr" in until and until["stderr"] in results["error"]
            terminates = terminates or nb_failings >= 5
            if not terminates:
                time.sleep(0.3)

    async def _command_setup(self, command: List[str], **kwargs):
        await self._execute_setup(command, **kwargs)

    async def _sleep_setup(self, seconds: float):
        time.sleep(seconds)

    async def _act_setup(self, action_seq: List[Union[Dict[str, Any], str]]):
        # TODO
        raise NotImplementedError()

    async def _replay_setup(self, trajectory: str):
        """
        Args:
            trajectory (str): path to the replay trajectory file
        """

        # TODO
        raise NotImplementedError()

    async def _activate_window_setup(self, window_name: str, strict: bool = False, by_class: bool = False):
        if not window_name:
            raise Exception(f"Setup Open - Invalid path ({window_name}).")

        payload = json.dumps({"window_name": window_name, "strict": strict, "by_class": by_class})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/activate_window", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to activate window {window_name}. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    async def _close_window_setup(self, window_name: str, strict: bool = False, by_class: bool = False):
        if not window_name:
            raise Exception(f"Setup Open - Invalid path ({window_name}).")

        payload = json.dumps({"window_name": window_name, "strict": strict, "by_class": by_class})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/close_window", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to close window {window_name}. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    # Chrome setup
    async def _chrome_open_tabs_setup(self, urls_to_open: List[str]):
        host = self.vm_ip
        port = self.chromium_port  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        logger.info("Connect to Chrome @: %s", remote_debugging_url)
        logger.debug("PLAYWRIGHT ENV: %s", repr(os.environ))
        for attempt in range(15):
            if attempt > 0:
                time.sleep(5)

            browser = None
            async with async_playwright() as p:
                try:
                    browser = await p.chromium.connect_over_cdp(remote_debugging_url)
                    # break
                except Exception as e:
                    if attempt < 14:
                        logger.info(f"Attempt {attempt + 1}: Failed to connect, retrying. Error: {e}")
                        # time.sleep(10)
                        continue
                    else:
                        logger.info(f"Failed to connect after multiple attempts: {e}")
                        raise e
            
                logger.info("Browser: %s", browser)

                if not browser:
                    logger.info("Failed to connect to Chrome")
                    return

                logger.info("Opening %s...", urls_to_open)
                for i, url in enumerate(urls_to_open):
                    # Use the first context (which should be the only one if using default profile)
                    if i == 0:
                        context = browser.contexts[0]

                    page = await context.new_page()  # Create a new page (tab) within the existing context
                    try:
                        await page.goto(url, timeout=60000)
                    except:
                        logger.warning("Opening %s exceeds time limit", url)  # only for human test
                    logger.info(f"Opened tab {i + 1}: {url}")

                    if i == 0:
                        # clear the default tab
                        default_page = context.pages[0]
                        await default_page.close()

                # Do not close the context or browser; they will remain open after script ends
                return browser, context

    async def _chrome_close_tabs_setup(self, urls_to_close: List[str]):
        time.sleep(5)  # Wait for Chrome to finish launching

        host = self.vm_ip
        port = self.chromium_port  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        async with async_playwright() as p:
            browser = None
            for attempt in range(15):
                try:
                    browser = await p.chromium.connect_over_cdp(remote_debugging_url)
                    # break
                except Exception as e:
                    if attempt < 14:
                        logger.error(f"Attempt {attempt + 1}: Failed to connect, retrying. Error: {e}")
                        time.sleep(5)
                    else:
                        logger.error(f"Failed to connect after multiple attempts: {e}")
                        raise e

            if not browser:
                return

            for i, url in enumerate(urls_to_close):
                # Use the first context (which should be the only one if using default profile)
                if i == 0:
                    context = browser.contexts[0]

                for page in context.pages:

                    # if two urls are the same, close the tab
                    if compare_urls(page.url, url):
                        context.pages.pop(context.pages.index(page))
                        await page.close()
                        logger.info(f"Closed tab {i + 1}: {url}")
                        break

            # Do not close the context or browser; they will remain open after script ends
            return browser, context

    # google drive setup
    async def _googledrive_setup(self, **config):
        """ Clean google drive space (eliminate the impact of previous experiments to reset the environment)
        @args:
            config(Dict[str, Any]): contain keys
                settings_file(str): path to google drive settings file, which will be loaded by pydrive.auth.GoogleAuth()
                operation(List[str]): each operation is chosen from ['delete', 'upload']
                args(List[Dict[str, Any]]): parameters for each operation
            different args dict for different operations:
                for delete:
                    query(str): query pattern string to search files or folder in google drive to delete, please refer to
                        https://developers.google.com/drive/api/guides/search-files?hl=en about how to write query string.
                    trash(bool): whether to delete files permanently or move to trash. By default, trash=false, completely delete it.
                for mkdirs:
                    path(List[str]): the path in the google drive to create folder
                for upload:
                    path(str): remote url to download file
                    dest(List[str]): the path in the google drive to store the downloaded file
        """
        settings_file = config.get('settings_file', 'evaluation_examples/settings/googledrive/settings.yml')
        gauth = GoogleAuth(settings_file=settings_file)
        drive = GoogleDrive(gauth)

        def mkdir_in_googledrive(paths: List[str]):
            paths = [paths] if type(paths) != list else paths
            parent_id = 'root'
            for p in paths:
                q = f'"{parent_id}" in parents and title = "{p}" and mimeType = "application/vnd.google-apps.folder" and trashed = false'
                folder = drive.ListFile({'q': q}).GetList()
                if len(folder) == 0:  # not exists, create it
                    parents = {} if parent_id == 'root' else {'parents': [{'id': parent_id}]}
                    file = drive.CreateFile({'title': p, 'mimeType': 'application/vnd.google-apps.folder', **parents})
                    file.Upload()
                    parent_id = file['id']
                else:
                    parent_id = folder[0]['id']
            return parent_id

        for oid, operation in enumerate(config['operation']):
            if operation == 'delete':  # delete a specific file
                # query pattern string, by default, remove all files/folders not in the trash to the trash
                params = config['args'][oid]
                q = params.get('query', '')
                trash = params.get('trash', False)
                q_file = f"( {q} ) and mimeType != 'application/vnd.google-apps.folder'" if q.strip() else "mimeType != 'application/vnd.google-apps.folder'"
                filelist: GoogleDriveFileList = drive.ListFile({'q': q_file}).GetList()
                q_folder = f"( {q} ) and mimeType = 'application/vnd.google-apps.folder'" if q.strip() else "mimeType = 'application/vnd.google-apps.folder'"
                folderlist: GoogleDriveFileList = drive.ListFile({'q': q_folder}).GetList()
                for file in filelist:  # first delete file, then folder
                    file: GoogleDriveFile
                    if trash:
                        file.Trash()
                    else:
                        file.Delete()
                for folder in folderlist:
                    folder: GoogleDriveFile
                    # note that, if a folder is trashed/deleted, all files and folders in it will be trashed/deleted
                    if trash:
                        folder.Trash()
                    else:
                        folder.Delete()
            elif operation == 'mkdirs':
                params = config['args'][oid]
                mkdir_in_googledrive(params['path'])
            elif operation == 'upload':
                params = config['args'][oid]
                url = params['url']
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmpf:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmpf.write(chunk)
                    tmpf.close()
                    paths = [params['path']] if params['path'] != list else params['path']
                    parent_id = mkdir_in_googledrive(paths[:-1])
                    parents = {} if parent_id == 'root' else {'parents': [{'id': parent_id}]}
                    file = drive.CreateFile({'title': paths[-1], **parents})
                    file.SetContentFile(tmpf.name)
                    file.Upload()
                return
            else:
                raise ValueError('[ERROR]: not implemented clean type!')

    async def _login_setup(self, **config):
        """ Login to a website with account and password information.
        @args:
            config(Dict[str, Any]): contain keys
                settings_file(str): path to the settings file
                platform(str): platform to login, implemented platforms include:
                    googledrive: https://drive.google.com/drive/my-drive

        """
        host = self.vm_ip
        port = self.chromium_port

        remote_debugging_url = f"http://{host}:{port}"
        async with async_playwright() as p:
            browser = None
            for attempt in range(15):
                try:
                    browser = await p.chromium.connect_over_cdp(remote_debugging_url)
                    # break
                except Exception as e:
                    if attempt < 14:
                        logger.error(f"Attempt {attempt + 1}: Failed to connect, retrying. Error: {e}")
                        time.sleep(5)
                    else:
                        logger.error(f"Failed to connect after multiple attempts: {e}")
                        raise e
            if not browser:
                return

            context = browser.contexts[0]
            platform = config['platform']

            if platform == 'googledrive':
                url = 'https://drive.google.com/drive/my-drive'
                page = await context.new_page()  # Create a new page (tab) within the existing context
                try:
                    await page.goto(url, timeout=60000)
                except:
                    logger.warning("Opening %s exceeds time limit", url)  # only for human test
                logger.info(f"Opened new page: {url}")
                settings = json.load(open(config['settings_file']))
                email, password = settings['email'], settings['password']

                try:
                    await page.wait_for_selector('input[type="email"]', state="visible", timeout=3000)
                    await page.fill('input[type="email"]', email)
                    await page.click('#identifierNext > div > button')
                    await page.wait_for_selector('input[type="password"]', state="visible", timeout=5000)
                    await page.fill('input[type="password"]', password)
                    await page.click('#passwordNext > div > button')
                    await page.wait_for_load_state('load', timeout=5000)
                except TimeoutError:
                    logger.info('[ERROR]: timeout when waiting for google drive login page to load!')
                    return

            else:
                raise NotImplementedError

            return browser, context

    async def _update_browse_history_setup(self, **config):
        cache_path = os.path.join(self.cache_dir, "history_new.sqlite")
        db_url = "https://drive.usercontent.google.com/u/0/uc?id=1Lv74QkJYDWVX0RIgg0Co-DUcoYpVL0oX&export=download" # google drive
        if not os.path.exists(cache_path):
                max_retries = 3
                downloaded = False
                e = None
                for i in range(max_retries):
                    try:
                        response = requests.get(db_url, stream=True)
                        response.raise_for_status()

                        with open(cache_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        logger.info("File downloaded successfully")
                        downloaded = True
                        break

                    except requests.RequestException as e:
                        logger.error(
                            f"Failed to download {db_url} caused by {e}. Retrying... ({max_retries - i - 1} attempts left)")
                if not downloaded:
                    raise requests.RequestException(f"Failed to download {db_url}. No retries left. Error: {e}")
        else:
            logger.info("File already exists in cache directory")
        # copy a new history file in the tmp folder
        db_path = cache_path

        history = config['history']

        for history_item in history:
            url = history_item['url']
            title = history_item['title']
            visit_time = datetime.now() - timedelta(seconds=history_item['visit_time_from_now_in_seconds'])

            # Chrome use ms from 1601-01-01 as timestamp
            epoch_start = datetime(1601, 1, 1)
            chrome_timestamp = int((visit_time - epoch_start).total_seconds() * 1000000)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                   INSERT INTO urls (url, title, visit_count, typed_count, last_visit_time, hidden)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url, title, 1, 0, chrome_timestamp, 0))

            url_id = cursor.lastrowid

            cursor.execute('''
                   INSERT INTO visits (url, visit_time, from_visit, transition, segment_id, visit_duration)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url_id, chrome_timestamp, 0, 805306368, 0, 0))

            conn.commit()
            conn.close()

        logger.info('Fake browsing history added successfully.')

        controller = PythonController(self.vm_ip, self.server_port)

        # get the path of the history file according to the platform
        os_type = controller.get_vm_platform()

        if os_type == 'Windows':
            chrome_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('USERPROFILE'), "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Darwin':
            chrome_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('HOME'), "Library", "Application Support", "Google", "Chrome", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Linux':
            if "arm" in platform.machine():
                chrome_history_path = controller.execute_python_command(
                    "import os; print(os.path.join(os.getenv('HOME'), 'snap', 'chromium', 'common', 'chromium', 'Default', 'History'))")[
                    'output'].strip()
            else:
                chrome_history_path = controller.execute_python_command(
                    "import os; print(os.path.join(os.getenv('HOME'), '.config', 'google-chrome', 'Default', 'History'))")[
                    'output'].strip()
        else:
            raise Exception('Unsupported operating system')

        form = MultipartEncoder({
            "file_path": chrome_history_path,
            "file_data": (os.path.basename(chrome_history_path), open(db_path, "rb"))
        })
        headers = {"Content-Type": form.content_type}
        logger.debug(form.content_type)

        # send request to server to upload file
        try:
            logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
            response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to upload file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

        self._execute_setup(["sudo chown -R user:user /home/user/.config/google-chrome/Default/History"], shell=True)
