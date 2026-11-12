# Tests for real caller threads across the round-robin LLM dispatch boundary.

import multiprocessing
import threading
import traceback
from collections import defaultdict
from queue import Queue
from unittest.mock import patch

import pytest
from cerebrum.llm.apis import LLMQuery

from aios.hooks.stores.queue import addMessage, getMessage
from aios.llm_core.adapter import LLMAdapter, LLMConfig
from aios.llm_core.routing import SequentialRouting
from aios.scheduler.rr_scheduler import RRScheduler
from aios.syscall.syscall import SyscallExecutor


def _exercise_readers(suspend_once, connection):
    """Run bounded real threads without starting providers or services."""
    entered = threading.Event()
    release = threading.Event()
    enqueued = threading.Event()
    stopping = threading.Event()
    lock = threading.Lock()
    queue = Queue()
    calls = []
    results = {}
    failures = []
    generations = defaultdict(int)
    readers = []
    scheduler = None
    old_hook = threading.excepthook

    def thread_failed(args):
        """Retain worker errors instead of losing them behind a timeout."""
        failures.append(f"{args.exc_type.__name__}: {args.exc_value}")

    def enqueue(syscall):
        """Wire the executor to an isolated real request queue."""
        with lock:
            calls.append(syscall)
            if len(calls) >= 2:
                enqueued.set()
        if stopping.is_set():
            syscall.set_status("done")
            syscall.event.set()
        else:
            addMessage(queue, syscall)

    def generate(**kwargs):
        """Only provider generation is simulated, not response processing."""
        syscall = kwargs["llm_syscall"]
        name = syscall.agent_name
        generations[name] += 1
        entered.set()
        assert release.wait(5), "test did not release simulated generation"
        finished = not suspend_once or generations[name] > 1
        if stopping.is_set():
            finished = True
        return f"reply:{name}:{generations[name]}", finished

    def read_response(name):
        """Use the actual executor, syscall wait/join, and retry loop."""
        try:
            query = LLMQuery(messages=[{"role": "user", "content": name}])
            results[name] = executor.execute_llm_syscall(name, query)
        except BaseException:
            failures.append(traceback.format_exc())

    queue_patch = patch(
        "aios.syscall.syscall.global_llm_req_queue_add_message", enqueue
    )
    error = None
    try:
        threading.excepthook = thread_failed
        adapter = object.__new__(LLMAdapter)
        adapter.llm_configs = [LLMConfig(name="test-model", backend="test")]
        adapter.llms = ["test-model"]
        adapter.available_llm_names = ["test-model"]
        adapter.router = SequentialRouting(adapter.llm_configs)
        adapter._get_model_response = generate
        other_queues = [Queue() for _ in range(3)]
        scheduler = RRScheduler(
            llm=adapter,
            memory_manager=None,
            storage_manager=None,
            tool_manager=None,
            log_mode="console",
            get_llm_syscall=lambda: getMessage(queue),
            get_memory_syscall=lambda: getMessage(other_queues[0]),
            get_storage_syscall=lambda: getMessage(other_queues[1]),
            get_tool_syscall=lambda: getMessage(other_queues[2]),
            time_slice=0.05,
        )
        executor = SyscallExecutor()
        queue_patch.start()
        scheduler.start()
        for name in ("first", "second"):
            reader = threading.Thread(target=read_response, args=(name,))
            readers.append(reader)
            reader.start()
        assert enqueued.wait(5), "callers did not enter the real queue"
        assert entered.wait(5), f"dispatch failed: {failures}"
        assert not failures
        assert not results, "caller returned before generation completed"
        assert all(reader.is_alive() for reader in readers)
        assert not any(syscall.event.is_set() for syscall in calls)
        release.set()
        for reader in readers:
            reader.join(5)
        assert not any(reader.is_alive() for reader in readers)
        assert not failures
        rounds = 2 if suspend_once else 1
        assert len(calls) == 2 * rounds
        pids = []
        for name in ("first", "second"):
            own_calls = [c for c in calls if c.agent_name == name]
            assert len(own_calls) == rounds
            assert len({id(c) for c in own_calls}) == rounds
            assert len({c.get_pid() for c in own_calls}) == 1
            pids.append(own_calls[0].get_pid())
            assert generations[name] == rounds
            response = results[name]["response"]
            assert response.response_message == f"reply:{name}:{rounds}"
            assert response.finished is True
            assert response.status_code == 200
            assert own_calls[-1].get_status() == "done"
            if suspend_once:
                assert own_calls[0].get_status() == "suspend"
            for syscall in own_calls:
                assert syscall.event.is_set()
                assert not syscall.is_alive()
                assert syscall.get_response() is not None
                assert syscall.get_start_time() <= syscall.get_end_time()
        assert pids[0] != pids[1]
        assert queue.empty()
    except BaseException:
        error = traceback.format_exc()
    finally:
        stopping.set()
        release.set()
        if scheduler is not None:
            scheduler.active = False
        with lock:
            for syscall in calls:
                syscall.set_status("done")
                syscall.event.set()
        for reader in readers:
            reader.join(5)
        if scheduler is not None:
            scheduler.stop()
        queue_patch.stop()
        threading.excepthook = old_hook
        if any(reader.is_alive() for reader in readers):
            error = (error or "") + "\nreader thread survived cleanup"
        connection.send(error)
        connection.close()


@pytest.mark.parametrize("suspend_once", [False, True])
def test_rr_dispatch_wakes_real_callers(suspend_once):
    """Completion and simulated suspension must reach waiting callers."""
    # The historical dispatch bug kills a scheduler worker while the reader
    # waits forever. Bound the whole scenario, including failure cleanup.
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=_exercise_readers, args=(suspend_once, sender)
    )
    process.start()
    sender.close()
    try:
        process.join(60)
        assert not process.is_alive(), "lifecycle subprocess exceeded 60s"
        assert process.exitcode == 0
        assert receiver.poll(1), "lifecycle subprocess returned no result"
        error = receiver.recv()
        assert error is None, error
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        if process.is_alive():
            process.kill()
            process.join(5)
        receiver.close()
        process.close()
