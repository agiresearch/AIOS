def foreach(op, objects, *args, **kwargs):
    if hasattr(op, '__call__'):
        return [op(obj, *args, **kwargs) for obj in objects]

    if isinstance(op, str):
        if op.startswith('.'):
            return [getattr(obj, op[1:]) for obj in objects]
        elif op.startswith('#'):
            return [getattr(obj, op[1:])(*args, **kwargs) for obj in objects]
        else:
            assert False
    assert False
