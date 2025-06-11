import os
from typing import Union


async def get_vm_screen_size(env, config: dict) -> dict:
    return await env.controller.get_vm_screen_size()


async def get_vm_window_size(env, config: dict) -> dict:
    return await env.controller.get_vm_window_size(app_class_name=config["app_class_name"])


async def get_vm_wallpaper(env, config: dict) -> Union[str, bytes]:
    _path = os.path.join(env.cache_dir, config["dest"])

    content = env.controller.get_vm_wallpaper()
    with open(_path, "wb") as f:
        f.write(content)

    return _path


async def get_list_directory(env, config: dict) -> dict:
    return await env.controller.get_vm_directory_tree(config["path"])
