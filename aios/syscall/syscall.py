import time
import json
from typing import Dict, List, Any, Optional

# Update import to use the new location
from aios.memory.note import MemoryNote
from aios.syscall import Syscall
from aios.syscall.llm import LLMSyscall
from aios.syscall.storage import StorageSyscall, storage_syscalls
from aios.syscall.tool import ToolSyscall
from aios.syscall.memory import MemorySyscall
from aios.hooks.stores._global import (
    global_llm_req_queue_add_message,
    global_memory_req_queue_add_message,
    global_storage_req_queue_add_message,
    global_tool_req_queue_add_message
)

import threading

from aios.hooks.types.llm import LLMRequestQueue
from aios.hooks.types.memory import MemoryRequestQueue
from aios.hooks.types.storage import StorageRequestQueue
from aios.hooks.types.tool import ToolRequestQueue

from cerebrum.llm.apis import LLMQuery, LLMResponse
from cerebrum.memory.apis import MemoryQuery, MemoryResponse
from cerebrum.storage.apis import StorageQuery, StorageResponse
from cerebrum.tool.apis import ToolQuery, ToolResponse

class SyscallExecutor:
    """
    A class that handles system call execution for different types of operations.
    
    This class provides methods to execute system calls for storage, memory,
    tools, and LLM operations, managing their lifecycle and responses.
    
    Example:
        ```python
        executor = SyscallExecutor()
        response = executor.execute_request("agent_1", LLMQuery(...))
        ```
    """
    
    def __init__(self):
        """Initialize the SyscallExecutor."""
        self.id = 0
        self.id_lock = threading.Lock()
    
    def create_syscall(self, agent_name: str, query) -> Dict[str, Any]:
        """
        Create a syscall object based on the query type.
        """
        if isinstance(query, LLMQuery):
            return LLMSyscall(agent_name, query)
        elif isinstance(query, StorageQuery):
            return StorageSyscall(agent_name, query)
        elif isinstance(query, MemoryQuery):
            return MemorySyscall(agent_name, query)
        elif isinstance(query, ToolQuery):
            return ToolSyscall(agent_name, query)

    def _execute_syscall(self, agent_name: str, query) -> Dict[str, Any]:
        """
        Execute a system call and collect timing metrics.
        
        Args:
            syscall: The system call object to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            syscall = StorageSyscall("agent_1", query)
            result = executor._execute_syscall(syscall)
            # Returns:
            {
                "response": "Operation completed",
                "start_times": [1234567890.123],
                "end_times": [1234567890.234],
                "waiting_times": [0.111],
                "turnaround_times": [0.222]
            }
            ```
        """
        completed_response = ""
        start_times, end_times = [], []
        waiting_times, turnaround_times = [], []

        with self.id_lock:
            self.id += 1
            syscall_id = self.id
        
        while True:
            # syscall = copy.deepcopy(syscall)
            syscall = self.create_syscall(agent_name, query)
            syscall.set_status("active")
            
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            if not syscall.get_source():
                syscall.set_source(syscall.agent_name)
            
            if not syscall.get_pid():
                syscall.set_pid(syscall_id)
            
            if isinstance(syscall, LLMSyscall):
                global_llm_req_queue_add_message(syscall)
                print(f"Syscall {syscall.agent_name} added to LLM queue")
                
            elif isinstance(syscall, StorageSyscall):
                global_storage_req_queue_add_message(syscall)
            elif isinstance(syscall, MemorySyscall):
                global_memory_req_queue_add_message(syscall)
            elif isinstance(syscall, ToolSyscall):
                global_tool_req_queue_add_message(syscall)
            
            syscall.start()
            syscall.join()
            
            # breakpoint()

            completed_response = syscall.get_response()
            
            if syscall.get_status() == "done":
                break
            
            # breakpoint()
            
            # Calculate timing metrics
            start_time = syscall.get_start_time()
            end_time = syscall.get_end_time()
            waiting_time = start_time - syscall.get_created_time()
            turnaround_time = end_time - syscall.get_created_time()

            start_times.append(start_time)
            end_times.append(end_time)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)

        return {
            "response": completed_response,
            "start_times": start_times,
            "end_times": end_times,
            "waiting_times": waiting_times,
            "turnaround_times": turnaround_times,
        }

    def execute_storage_syscall(self, agent_name: str, query: StorageQuery) -> Dict[str, Any]:
        """
        Execute a storage system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: Storage query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = StorageQuery(operation_type="read", params={"path": "/tmp/file.txt"})
            result = executor.execute_storage_syscall("agent_1", query)
            ```
        """
        # syscall = StorageSyscall(agent_name, query)
        # syscall.set_target("storage")
        # global_storage_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_memory_syscall(self, agent_name: str, query: MemoryQuery) -> Dict[str, Any]:
        """
        Execute a memory system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: Memory query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = MemoryQuery(operation="store", data={"key": "value"})
            result = executor.execute_memory_syscall("agent_1", query)
            ```
        """
        # syscall = Syscall(agent_name, query)
        # syscall.set_target("memory")
        # global_memory_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_tool_syscall(self, agent_name: str, query: ToolQuery) -> Dict[str, Any]:
        """
        Execute a tool system call.
        
        Args:
            agent_name: Name of the agent making the request
            tool_calls: List of tool calls to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            tool_calls = [{"name": "calculator", "arguments": {"operation": "add", "numbers": [1, 2]}}]
            result = executor.execute_tool_syscall("agent_1", tool_calls)
            ```
        """
        # syscall = ToolSyscall(agent_name, tool_calls)
        # syscall.set_target("tool")
        # global_tool_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_llm_syscall(self, agent_name: str, query: LLMQuery) -> Dict[str, Any]:
        """
        Execute an LLM system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: LLM query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = LLMQuery(messages=[{"role": "user", "content": "Hello"}], action_type="chat")
            result = executor.execute_llm_syscall("agent_1", query)
            ```
        """
        # syscall = LLMSyscall(agent_name=agent_name, query=query)
        # syscall.set_target("llm")
        # global_llm_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_file_operation(self, agent_name: str, query: LLMQuery) -> str:
        """
        Execute a file system operation using LLM parsing.
        
        Args:
            agent_name: Name of the agent making the request
            query: LLM query containing file operation instructions
            
        Returns:
            String containing operation summary
            
        Example:
            ```python
            query = LLMQuery(
                messages=[{"role": "user", "content": "Create a file named test.txt"}],
                action_type="operate_file"
            )
            result = executor.execute_file_operation("agent_1", query)
            ```        """
        # Parse file system operation
        system_prompt = "You are a parser for parsing file system operations. Your task is to parse the instructions and return the file system operation call."
        query.messages = [{"role": "system", "content": system_prompt}] + query.messages
        query.tools = storage_syscalls
        
        
        parser_response = self.execute_llm_syscall(agent_name, query)["response"]
        file_operations = parser_response.tool_calls
        
        # breakpoint()
        
        operation_summaries = []
        
        # Execute each file operation
        for operation in file_operations:
            storage_query = StorageQuery(
                operation_type=operation.get("name"),
                params=operation.get("parameters")
            )
            
            # breakpoint()
            storage_response = self.execute_storage_syscall(agent_name, storage_query)
            
            # Summarize operation result
            summary_query = LLMQuery(
                messages=[{
                    "role": "user",
                    "content": f"Tell me what you have done from {storage_response} with a friendly tone. "
                              f"Try to be concise and maintain the key information including file name, file path, etc"
                }],
                action_type="chat"
            )
            summary = self.execute_llm_syscall(agent_name, summary_query)["response"].response_message
            operation_summaries.append(summary)
        
        # Generate final summary
        final_query = LLMQuery(
            messages=[{
                "role": "user",
                "content": f"Tell me what you have done from {json.dumps(operation_summaries)} with a friendly tone. "
                          f"Try to be concise and maintain the key information including file name, file path, etc"
            }],
            action_type="chat"
        )
        
        return self.execute_llm_syscall(agent_name, final_query)["response"].response_message

    def execute_memory_content_analyze(self, agent_name: str, query: MemoryQuery) -> Dict[str, Any]:
        """
        Generate a structured analysis result for a memory query.
        
        Args:
            agent_name: Name of the agent making the request
            query: Memory query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = MemoryQuery(operation="store", data={"key": "value"})
            result = executor.execute_memory_content_analyze("agent_1", query)
            ```
        """
        content = query.params.get("content", {})
        system_prompt = """Generate a structured analysis result, including:
             1. Identify the most important keywords (focus on nouns, verbs, and key concepts)
             2. Extract core topics and context elements
             3. Create relevant classification tags
 
             Format the response as a JSON object:
             {
                 "keywords": [
                     // Several specific, different keywords, capturing key concepts and terms
                     // Sorted by importance
                     // Do not include keywords that are the speaker or time
                     // At least three keywords, but not too redundant.
                 ],
                 "context": 
                     // A one-sentence summary:
                     // - Topic/domain
                     // - Key points/main arguments
                     // - Target audience/purpose
                 ,
                 "tags": [
                     // Several broad classification/topics
                     // Including domain, format, and type tags
                     // At least three tags, but not too redundant.
                 ]
             }
 
             Content analysis:
         """
        response_format = {
            "type": "json_schema", 
            "json_schema": {
                "name": "response",
                "schema": {
                    "type": "object",
                     "properties": {
                         "keywords": {
                             "type": "array",
                             "items": {
                                 "type": "string"
                             }
                         },
                         "context": {
                             "type": "string"
                         },
                         "tags": {
                             "type": "array",
                             "items": {
                                 "type": "string"
                             }
                         }
                     }
                 }
             }
        }
        
        messages = [{"role": "system", "content": "You should reply with the json object only."}] + [{"role": "user", "content": system_prompt + content}]
        message_return_type = "json"
        response_format = response_format
        query_llm = LLMQuery(
            messages=messages,
            action_type="chat",
            message_return_type=message_return_type,
            response_format=response_format
        )
        response = self.execute_llm_syscall(agent_name, query_llm)["response"]
        
        # Get the response message and parse JSON
        response_message = response.response_message
        print("response_message:", response_message)
        try:
            # Try to parse the JSON response
            if isinstance(response_message, str):
                # Check if the JSON string is too long, truncate if necessary
                if len(response_message) > 10000:  # Set a reasonable length limit
                    print(f"Warning: Response too long ({len(response_message)} chars), truncating...")
                    # Try to find the last complete JSON object
                    last_brace_pos = response_message.rfind('}')
                    if last_brace_pos > 0:
                        response_message = response_message[:last_brace_pos+1]
                
                import json
                try:
                    parsed_response = json.loads(response_message)
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error: {json_err}")
                    # Try to fix common JSON format issues
                    # 1. Remove possible trailing commas
                    response_message = response_message.replace(',}', '}').replace(',]', ']')
                    # 2. Ensure strings are properly quoted
                    try:
                        parsed_response = json.loads(response_message)
                    except:
                        # If still unable to parse, create a minimal valid response
                        print("Failed to parse JSON after cleanup attempts, using default values")
                        return {"keywords": ["memory", "test"], "context": "", "tags": ["memory", "test"]}
            elif isinstance(response_message, dict):
                parsed_response = response_message
            else:
                print(f"Invalid response format from LLM: {type(response_message)}")
                return {"keywords": [], "context": "", "tags": []}
                
            # Extract required fields
            keywords = parsed_response.get("keywords", [])
            context = parsed_response.get("context", "")
            tags = parsed_response.get("tags", [])
            
            # Ensure keywords and tags are list types
            if not isinstance(keywords, list):
                keywords = [str(keywords)] if keywords else []
            if not isinstance(tags, list):
                tags = [str(tags)] if tags else []
                
            # Limit the number of tags to avoid overly long tag lists
            if len(tags) > 20:
                tags = tags[:20]
                
            return {"keywords": keywords, "context": context, "tags": tags}
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Return default values when an error occurs
            return {"keywords": [], "context": "", "tags": []}

    def execute_memory_evolve(self, query: MemoryQuery, similar_memories: List[MemoryNote]) -> (MemoryQuery, Dict[str, Any]):
        """
        Evolve a memory query based on similar memories.
        
        Args:
            query: Memory query to evolve
            similar_memories: List of similar memories
            
        Returns:
            Tuple containing evolved query and response
            
        Example:
            ```python
            similar_memories = [memory1, memory2]
            evolved_query, response = executor.execute_memory_evolve(query, similar_memories)
            ```
        """
        try:
            nearest_neighbors_memories = "\n".join([
                f"memory id: {memory.id}, memory content: {memory.content}, tags: {', '.join(memory.tags)}, context: {memory.context}, keywords: {', '.join(memory.keywords)}" 
                for memory in similar_memories
            ])
        except Exception as e:
            print(f"Error processing similar memories: {e}")
            nearest_neighbors_memories = ""
        system_prompt = '''
        You are an AI memory evolution agent responsible for managing and evolving a knowledge base.
        Analyze the new memory note and its nearest neighbors to determine if and how it should evolve.
 
        New memory:
        Content: {content}
        Context: {context}
        Keywords: {keywords}
 
        Nearest neighbors:
        {nearest_neighbors_memories}
 
        Based on this information, determine:
        1. Should this memory evolve? Consider its relationships with other memories
        2. What type of evolution should occur?
        3. What specific changes should be made?
 
        Return your decision in JSON format:
        {{
            "should_evolve": true/false,
            "evolution_type": ["update", "merge"],
            "reasoning": "Explanation for the decision",
            "affected_memories": ["memory_ids"],
            "evolution_details": {{
                "new_context": "Updated context",
                "new_keywords": ["keyword1", "keyword2"],
                "new_relationships": ["rel1", "rel2"]
            }}
        }}
        '''.format(
            content=getattr(query, 'content', ''),
            context=getattr(query, 'context', ''),
            keywords=getattr(query, 'keywords', []),
            nearest_neighbors_memories=nearest_neighbors_memories
        )
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "should_evolve": {
                            "type": "string"
                        },
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "suggested_connections": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "new_context_neighborhood": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "tags_to_update": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "new_tags_neighborhood": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "corresponding_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["should_evolve", "actions", "suggested_connections", "tags_to_update", "new_context_neighborhood", "new_tags_neighborhood"]
                }
            }
        }
        
        query_llm = LLMQuery(
            messages=[
                {"role": "system", "content": "You should reply with the json object only."}, 
                {"role": "user", "content": system_prompt}
            ],
            action_type="chat",
            message_return_type="json",
            response_format=response_format
        )
        
        # Use the agent_name parameter passed in the query object
        agent_name = getattr(query, 'agent_name', "default_agent")
        
        try:
            llm_response = self.execute_llm_syscall(agent_name, query_llm)["response"]
            
            # Get the response message and parse it
            response_message = llm_response.response_message
            print("memory_evolve response:", response_message)
            
            # Try to parse the JSON response
            if isinstance(response_message, str):
                # Check if the JSON string is too long, truncate if necessary
                if len(response_message) > 10000:  # Set a reasonable length limit
                    print(f"Warning: Response too long ({len(response_message)} chars), truncating...")
                    # Try to find the last complete JSON object
                    last_brace_pos = response_message.rfind('}')
                    if last_brace_pos > 0:
                        response_message = response_message[:last_brace_pos+1]
                
                import json
                try:
                    response = json.loads(response_message)
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error: {json_err}")
                    # Try to fix common JSON format issues
                    # 1. Remove possible trailing commas
                    response_message = response_message.replace(',}', '}').replace(',]', ']')
                    # 2. Ensure strings are properly quoted
                    try:
                        response = json.loads(response_message)
                    except:
                        # If still unable to parse, return the original query and an empty list
                        print("Failed to parse JSON after cleanup attempts")
                        return (query, [])
            elif isinstance(response_message, dict):
                response = response_message
            else:
                print(f"Invalid response format from LLM: {type(response_message)}")
                return (query, [])
                
            should_evolve = response.get("should_evolve", "False")
            
            similar_memories = []
            if should_evolve.lower() == "true":
                for j in range(response.get("new_context_neighborhood", 0)):
                    similar_memories.append({"context": response.get("new_context_neighborhood")[j], "id": response.get("corresponding_ids")[j], "tags": response.get("new_tags_neighborhood")[j]})
            
            return (query, similar_memories)
                            
        except Exception as e:
            print(f"Error in execute_memory_evolve: {e}")
            import traceback
            traceback.print_exc()
            
        return (query, similar_memories)

    def execute_request(self, agent_name: str, query: Any) -> Dict[str, Any]:
        """
        Execute a request based on its type.
        
        Args:
            agent_name: Name of the agent making the request
            query: Query object of various types (LLM, Tool, Memory, Storage)
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = LLMQuery(messages=[{"role": "user", "content": "Hello"}], action_type="chat")
            result = executor.execute_request("agent_1", query)
            ```
        """
        if isinstance(query, LLMQuery):
            # breakpoint()
            if query.action_type == "chat" or query.action_type == "chat_with_json_output" or query.action_type == "chat_with_tool_call_output":
                llm_response = self.execute_llm_syscall(agent_name, query)
                return llm_response
            
            elif query.action_type == "call_tool":
                llm_response = self.execute_llm_syscall(agent_name, query)["response"]
                if llm_response.tool_calls == None or len(llm_response.tool_calls) == 0:
                    return ToolResponse(
                        response_message=f"No tool was called by LLM",
                        finished=False
                    )
                tool_query = ToolQuery(
                    tool_calls=llm_response.tool_calls,
                    # action_type="tool_use"
                )
                tool_response = self.execute_tool_syscall(agent_name, tool_query)
                return tool_response
            
            elif query.action_type == "operate_file":
                return self.execute_file_operation(agent_name, query)
        elif isinstance(query, ToolQuery):
            return self.execute_tool_syscall(agent_name, query)
        elif isinstance(query, MemoryQuery):
            if query.operation_type == "add_agentic_memory":
                metadata = self.execute_memory_content_analyze(agent_name, query)
                query.params.update(metadata)
                # retrieve the related memory and evolve the memory.
                query.operation_type = "retrieve_memory_raw"
                similar_memories = self.execute_memory_syscall(agent_name, query)
                print(similar_memories,type(similar_memories))
                query, similar_memories_evolved = self.execute_memory_evolve(query, similar_memories)
                # define a memory abstract in the memory layer.
                query.operation_type = "add_memory"
                if similar_memories_evolved != []:
                    for memory_params_dict in similar_memories_evolved:
                        updated_query = MemoryQuery()
                        updated_query.params = memory_params_dict # return a dict with full parameters, also with memory id for updated
                        updated_query.operation_type = "update_memory"
                        self.execute_memory_syscall(agent_name, updated_query)
                return self.execute_memory_syscall(agent_name, query)
            elif query.operation_type == "add_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.operation_type == "remove_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.operation_type == "update_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.operation_type == "retrieve_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.operation_type == "get_memory":
                return self.execute_memory_syscall(agent_name, query)
        elif isinstance(query, StorageQuery):
            return self.execute_storage_syscall(agent_name, query)

def create_syscall_executor():
    """
    Create and return a SyscallExecutor instance and its wrapper.
    
    Returns:
        Tuple of (execute_request function, SyscallWrapper class)
        
    Example:
        ```python
        executor, wrapper = create_syscall_executor()
        response = executor("agent_1", LLMQuery(...))
        ```
    """
    executor = SyscallExecutor()
    
    class SyscallWrapper:
        """Wrapper class providing direct access to syscall methods."""
        llm = executor.execute_llm_syscall
        storage = executor.execute_storage_syscall
        memory = executor.execute_memory_syscall
        tool = executor.execute_tool_syscall

    return executor.execute_request, SyscallWrapper

# Maintain backwards compatibility
useSysCall = create_syscall_executor
