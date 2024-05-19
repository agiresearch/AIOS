from abc import ABC, abstractmethod

class Benchmark(ABC):
    @abstractmethod
    def speed(self) -> tuple[float, float]:
        raise NotImplementedError

    @abstractmethod
    def length(self) -> tuple[int, int]:
        raise NotImplementedError


class GeminiBenchmark(Benchmark):
    def speed(self):
        return (0.4, 0.7)

    def length(self):
        return (450, 900)

class GPT35Benchmark(Benchmark):
    def speed(self):
        return (0.2, 0.4)

    def length(self):
        return (100, 600)

class ClaudeSonnetBenchmark(Benchmark):
    def speed(self):
        return (0.00, 0.3)

    def length(self):
        return (5, 30)