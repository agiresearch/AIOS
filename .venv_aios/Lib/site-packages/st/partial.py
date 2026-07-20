def partial_front(func, *para):
    def new_func(*args):
        return func(*(para + args))
    return new_func


def partial_back(func, *para):
    def new_func(*args):
        return func(*(args + para))
    return new_func


def zero_para(func):
    def new_func(*_):
        return func()
    new_func.__name__ = 'zero_para<{}>'.format(func.__name__)
    return new_func


def pack_para_front(*para):
    def pack(func):
        return partial_front(func, *para)
    return pack


def pack_para_back(*para):
    def pack(func):
        return partial_back(func, *para)
    return pack
