import zlib

class Compressor:
    def __init__(self) -> None:
        pass

    def compress(self, data):
        pass

    def decompress(self, compressed_data):
        pass

class ZLIBCompressor(Compressor):
    def __init__(self) -> None:
        pass

    def compress(self, data):
        compressed_data = zlib.compress(data.encode('utf-8'))
        return compressed_data

    def decompress(self, compressed_data):
        decompressed_data = zlib.decompress(compressed_data)
        return decompressed_data.decode('utf-8')
