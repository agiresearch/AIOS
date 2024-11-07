# global variables

from aios.hooks.modules.llm import useLLMRequestQueue

from aios.hooks.modules.memory import useMemoryRequestQueue

from aios.hooks.modules.storage import useStorageRequestQueue

from aios.hooks.modules.tool import useToolRequestQueue

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

(
    global_storage_req_queue,
    global_storage_req_queue_get_message,
    global_storage_req_queue_add_message,
    global_storage_req_queue_is_empty,
) = useStorageRequestQueue()

(
    global_tool_req_queue,
    global_tool_req_queue_get_message,
    global_tool_req_queue_add_message,
    global_tool_req_queue_is_empty
) = useToolRequestQueue()
