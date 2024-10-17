# global variables

from aios.hooks.modules.llm import useLLMRequestQueue

from aios.hooks.modules.memory import useMemoryRequestQueue

(
    global_llm_req_queue,
    global_llm_req_queue_get_message,
    global_llm_req_queue_add_message,
    global_llm_req_queue_is_empty,
) = useLLMRequestQueue()

(
    global_memory_req_queue,
    global_memory_req_queue_get_message,
    global_memory_req_queue_add_message,
    global_memory_req_queue_is_empty,
) = useMemoryRequestQueue()
