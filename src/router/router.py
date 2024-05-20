from src.router.benchmarks import ClaudeSonnetBenchmark, GPT35Benchmark, GeminiBenchmark 
from src.router.utils import get_intended_speed, get_token_length

class ModelRouter:
    benchmarks = {
        ClaudeSonnetBenchmark() : 'claude_sonnet',
        GPT35Benchmark() : 'gpt-3.5',
        GeminiBenchmark()  : 'gemini-pro',
    }

    @classmethod
    def evaluate(cls, phrase) -> str | None:
        speed = get_intended_speed(phrase)
        length = get_token_length(phrase)

        for benchmark, model in cls.benchmarks.items():
            if speed > benchmark.speed()[0] and speed <= benchmark.speed()[1] and length >= benchmark.length()[0] and length <= benchmark.length()[1]:
                return model
        return None