# This is a more generic test that ensures malloc is working.

import pytest
from src.memory.base import Memory

@pytest.fixture
def memory():
    return Memory(size=1024)

def test_mem_alloc(memory):
    addr1 = memory.mem_alloc(100)
    assert addr1 == 0

    addr2 = memory.mem_alloc(200)
    assert addr2 == 100

    with pytest.raises(MemoryError):
        memory.mem_alloc(1000)  # Not enough memory
