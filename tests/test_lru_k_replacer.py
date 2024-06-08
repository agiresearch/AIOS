# This tests the buffer manager that the project relies on. It manually 
# changes the access histories and entries to check all the edge cases.

from src.memory.lru_k_replacer import LRU_K_Replacer
import pytest

@pytest.fixture
def replacer():
    return LRU_K_Replacer(capacity=5, k=2)

def test_update_access_history(replacer):
    replacer.update_access_history(1)
    assert replacer.size() == 1
    assert replacer.entries[1].hit_count == 1

    replacer.update_access_history(1)
    assert replacer.size() == 1
    assert replacer.entries[1].hit_count == 2

    replacer.update_access_history(2)
    assert replacer.size() == 2
    assert replacer.entries[2].hit_count == 1

def test_evict(replacer):
    replacer.update_access_history(1)
    replacer.update_access_history(2)
    replacer.update_access_history(3)
    replacer.update_access_history(1)
    replacer.update_access_history(4)
    replacer.update_access_history(5)

    assert replacer.evict() == 2
    assert replacer.size() == 4

    assert replacer.evict() == 3
    assert replacer.size() == 3

def test_set_evictable(replacer):
    replacer.update_access_history(1)
    replacer.update_access_history(2)

    replacer.set_evictable(1, False)
    assert not replacer.entries[1].evictable
    assert replacer.size() == 1

    replacer.set_evictable(1, True)
    assert replacer.entries[1].evictable
    assert replacer.size() == 2

# def test_remove(replacer):
#     replacer.update_access_history(1)
#     replacer.update_access_history(2)
#     replacer.update_access_history(1)
#
#     replacer.remove(1)
#     assert 1 not in replacer.entries
#     assert replacer.size() == 1
#
#     with pytest.raises(ValueError):
#         replacer.remove(2)
#         replacer.set_evictable(2, False)
#         replacer.remove(2)

def test_invalid_block_id(replacer):
    with pytest.raises(ValueError):
        replacer.update_access_history(6)

    with pytest.raises(ValueError):
        replacer.set_evictable(6, True)
