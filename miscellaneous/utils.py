from contextlib import contextmanager
from datetime import datetime
from dateutil.parser import parse
from bson import ObjectId
from time import time
import dill
import os


def to_datetime(datetime_string):
    try:
        return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
    except:
        return parse(datetime_string)


def to_ch_datetime(datetime_obj):
    return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')


@contextmanager
def time_usage(item_name=""):
    tick = time()
    try:
        yield
    finally:
        print('{0}\ttime usage\t{1:,.4f}'.format(item_name, time() - tick))


def save(obj, file_path=None):
    if not file_path:
        file_id = str(ObjectId())
        file_path = '/resources/core/files/{}.pkl'.format(file_id)
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'wb') as file:
        dill.dump(obj, file)
    return file_path


def load(file_path):
    try:
        with open(file_path, 'rb') as file:
            obj = dill.load(file)
        return obj
    except Exception as e:
        print('Load Error: {}'.format(str(e)))
    return None
