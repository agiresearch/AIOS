import time

time_points = dict()


def set_time_point(key='default'):
    time_points[key] = time.time()


def microsecond_from(key='default'):
    return int((time.time() - time_points.get(key, time.time())) * 1000)
