"""
Regression tests: the LSFS keeps every requested path inside its root.

``aios/storage/filesystem/lsfs.py`` used to join ``root_dir`` only for
relative paths, so an absolute path or a ``..`` segment reached anything
on disk, and ``sto_share`` even uploaded a file from outside the root.
These cases pin the confinement: a relative path still lands inside the
root, and absolute paths, ``..``, ``sto_mount`` and ``sto_share`` pointing
outside are refused.

No network and no Redis are used: ``redis`` and ``watchdog`` are in-memory
doubles, the vector database is a stub and the share upload is captured
instead of being sent.
"""
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

# In-memory doubles for the modules LSFS imports at load time.
redis_mod = types.ModuleType("redis")


class _Redis:
    def __init__(self):
        self.kv = {}

    def ping(self):
        return True

    def hgetall(self, key):
        return self.kv.get(key, {})

    def hmset(self, key, value):
        self.kv[key] = dict(value)

    def expire(self, key, seconds):
        return True


redis_mod.Redis = lambda **kwargs: _Redis()
redis_mod.ConnectionError = type("ConnectionError", (Exception,), {})
sys.modules.setdefault("redis", redis_mod)

watchdog_mod = types.ModuleType("watchdog")
observers_mod = types.ModuleType("watchdog.observers")
events_mod = types.ModuleType("watchdog.events")


class _Observer:
    def schedule(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass


observers_mod.Observer = _Observer
events_mod.FileSystemEventHandler = type("FileSystemEventHandler", (), {})
sys.modules.setdefault("watchdog", watchdog_mod)
sys.modules.setdefault("watchdog.observers", observers_mod)
sys.modules.setdefault("watchdog.events", events_mod)

# The vector database is not needed: every test builds LSFS with
# use_vector_db=False, except the mount case, which replaces it anyway.
vector_db_mod = types.ModuleType("aios.storage.filesystem.vector_db")
vector_db_mod.get_vector_db = lambda mount_dir=None: None
sys.modules.setdefault("aios.storage.filesystem.vector_db", vector_db_mod)

# aios.config is imported for real: CI copies config.yaml.example to
# aios/config/config.yaml before running the tests, and replacing the module
# here would leak into every other test in the same process.

from aios.storage.filesystem.lsfs import LSFS  # noqa: E402


class _VectorDb:
    def __init__(self):
        self.mounted = []

    def add_or_get_collection(self, name):
        return name

    def build_database(self, root):
        self.mounted.append(root)


class LsfsPathConfinementTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aios-lsfs-")
        self.base = self._tmp.name
        self.root = os.path.join(self.base, "root")
        self.outside = os.path.join(self.base, "outside")
        os.makedirs(self.root)
        os.makedirs(self.outside)
        self.lsfs = LSFS(root_dir=self.root, use_vector_db=False)

    def tearDown(self):
        # Stop the file-system observer the LSFS starts, so no thread leaks.
        if hasattr(self.lsfs, "observer"):
            self.lsfs.observer.stop()
            self.lsfs.observer.join()
        self._tmp.cleanup()

    # Positive control: a normal relative path keeps working.
    def test_relative_path_is_still_written_inside_root(self):
        result = self.lsfs.sto_write(file_name=None, file_path="inside.txt", content="ok")
        self.assertTrue(os.path.exists(os.path.join(self.root, "inside.txt")), result)

    def test_absolute_path_outside_root_is_refused(self):
        target = os.path.join(self.outside, "written.txt")
        result = self.lsfs.sto_write(file_name=None, file_path=target, content="escape")
        self.assertFalse(os.path.exists(target), f"wrote outside the root: {result}")

    def test_dotdot_path_outside_root_is_refused(self):
        self.lsfs.sto_write(file_name=None, file_path="../escape.txt", content="x")
        self.assertFalse(os.path.exists(os.path.join(self.base, "escape.txt")))

    def test_create_file_absolute_outside_root_is_refused(self):
        target = os.path.join(self.outside, "new.txt")
        self.lsfs.sto_create_file(file_name=None, file_path=target)
        self.assertFalse(os.path.exists(target))

    def test_create_directory_absolute_outside_root_is_refused(self):
        target = os.path.join(self.outside, "newdir")
        self.lsfs.sto_create_directory(dir_name=None, dir_path=target)
        self.assertFalse(os.path.exists(target))

    def test_mount_outside_root_is_refused(self):
        vector_db = _VectorDb()
        self.lsfs.vector_db = vector_db
        self.lsfs.sto_mount(collection_name="agent", root_dir=self.outside)
        self.assertEqual(vector_db.mounted, [])

    def test_share_does_not_upload_file_outside_root(self):
        target = os.path.join(self.outside, "secret.txt")
        with open(target, "w") as handle:
            handle.write("token=SECRET")
        sent = []
        with mock.patch.object(
            self.lsfs, "generate_share_link", side_effect=lambda p: sent.append(p) or "link"
        ):
            result = self.lsfs.sto_share(file_path=target)
        self.assertEqual(sent, [], f"shared a file from outside the root: {json.dumps(result)[:120]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
