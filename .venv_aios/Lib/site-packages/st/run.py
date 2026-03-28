import types
import hashlib
modules = dict()


def run(code: str, key: str=None, **kwargs):
    md5 = hashlib.md5(code.encode()).hexdigest()
    if md5 not in modules:
        module = types.ModuleType(md5)
        for k, v in kwargs.items():
            setattr(module, k, v)
        exec(code, module.__dict__)
        modules[md5] = module
    else:
        module = modules[md5]
    if key:
        return getattr(module, key)
    else:
        return module
