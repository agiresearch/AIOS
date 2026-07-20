class SingletonMetaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(cls):
    class SingletonClass(cls, metaclass=SingletonMetaclass):
        pass
    SingletonClass.__name__ = cls.__name__
    return SingletonClass
