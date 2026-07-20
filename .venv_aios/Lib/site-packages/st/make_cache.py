import os
import codecs


def get_cache_dir():
    current_dir = os.path.abspath(os.path.curdir)
    for i in range(3):
        if os.path.exists(os.path.join(current_dir, 'cache')):
            return os.path.join(current_dir, 'cache')
        current_dir = os.path.dirname(current_dir)
    cache_dir = os.path.join(os.path.abspath(os.path.curdir), 'cache')
    os.makedirs(cache_dir)
    return cache_dir


def get_file_name(filename: str):
    return os.path.splitext(os.path.split(filename)[-1])[0]


def get_cache_filename(filename: str):
    cache_dir = get_cache_dir()
    return os.path.join(cache_dir, get_file_name(filename) + '.cache')


def cache_valid(filename: str):
    cache_filename = get_cache_filename(filename)

    if os.path.exists(cache_filename):
        cache_time = os.stat(cache_filename).st_mtime
        if os.path.exists(filename):
            file_time = os.stat(filename).st_mtime
            if file_time > cache_time:
                return False
    else:
        if os.path.exists(filename):
            return False
        else:
            raise FileNotFoundError('Cache File Not Found')
    return True


def get_cache(filename: str):
    cache_filename = get_cache_filename(filename)
    with codecs.open(cache_filename, 'r', 'utf-8') as f:
        return f.read()


def set_cache(filename: str, value: object):
    cache_filename = get_cache_filename(filename)
    with codecs.open(cache_filename, 'w', 'utf-8') as f:
        f.write(value)


def make_cache(func):
    def cache_func(filename):
        if cache_valid(filename):
            return get_cache(filename)
        else:
            updated_result = func(filename)
            set_cache(filename, updated_result)
            return updated_result
    cache_func.__name__ = func.__name__
    return cache_func
