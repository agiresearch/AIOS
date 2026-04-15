import pickle
import binascii


def serialize(obj):
    return binascii.b2a_hex(pickle.dumps(obj)).decode()


def deserialize(string: str):
    return pickle.loads(binascii.a2b_hex(string.encode()))
