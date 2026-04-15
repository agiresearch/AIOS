from . import foreach


def chain(*func_list):
    def chain_func(*args, **kwargs):
        for func in reversed(func_list):
            if not isinstance(args, list) and not isinstance(args, tuple):
                args = (args, )
            args = func(*args, **kwargs)
            kwargs = {}
        return args

    chain_func.__name__ = 'chain<{0}>'.format(', '.join(foreach('.__name__', func_list)))
    return chain_func
