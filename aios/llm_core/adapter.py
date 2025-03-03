from aios.context.simple_context import SimpleContextManager
from aios.llm_core.strategy import RouterStrategy, SimpleStrategy
from aios.llm_core.local import HfLocalBackend, VLLMLocalBackend, OllamaBackend
from aios.utils.id_generator import generator_tool_call_id
from cerebrum.llm.apis import LLMQuery, LLMResponse
from litellm import completion
import json
from .utils import tool_calling_input_format, parse_json_format, parse_tool_calls, pre_process_tools
from typing import Dict, Optional, Any, List, Union
import time
import re
import os
from aios.config.config_manager import config
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """
    Data class to hold LLM configuration parameters.
    
    Attributes:
        name (str): Name of the LLM model
        backend (str): Backend type for the LLM
        max_gpu_memory (Optional[str]): Maximum GPU memory allocation
        eval_device (Optional[str]): Device for model evaluation
        hostname (Optional[str]): Hostname for the LLM service
    
    Example:
        ```python
        config = LLMConfig(
            name="gpt-4o-mini",
            backend="openai",
        )
        ```
    """
    name: str
    backend: Optional[str] = None
    max_gpu_memory: Optional[str] = None
    eval_device: Optional[str] = None
    hostname: Optional[str] = None

class LLMAdapter:
    """
    The LLMAdapter class is an abstraction layer that represents the LLM router.
    This router allows load-balancing of multiple varying endpoints so that
    multiple requests can be handled at once.
    
    Example:
        ```python
        configs = [
            {
                "name": "gpt-4o-mini",
                "backend": "openai",
            }, # OpenAI
            {
                "name": "qwen2.5:7b",
                "backend": "ollama",
                "hostname": "http://localhost:11434"
            }, # Ollama
            {
                "name": "mistral-7b",
                "backend": "hflocal",
                "max_gpu_memory": "12GiB"
            } # Hugging Face Local
        ]
        adapter = LLMAdapter(
            llm_configs=configs,
            log_mode="console",
            use_context_manager=True
        )
        ```
    """

    def __init__(
        self,
        llm_configs: List[Dict[str, Any]],
        api_key: Optional[Union[str, List[str]]] = None,
        log_mode: str = "console",
        use_context_manager: bool = False,
        strategy: Optional[RouterStrategy] = RouterStrategy.SIMPLE,
    ):
        """
        Initialize the LLMAdapter.

        Args:
            llm_configs: List of LLM configurations
            api_key: API key(s) for the LLM services
            log_mode: Mode of logging the LLM processing status
            use_context_manager: Whether to use context management
            strategy: Strategy for routing requests
        """
        self.log_mode = log_mode
        self.use_context_manager = use_context_manager
        self.context_manager = SimpleContextManager() if use_context_manager else None
        self.llm_configs = llm_configs
        self.llms = []
        
        self._setup_api_keys()
        self._initialize_llms()
        
        if strategy == RouterStrategy.SIMPLE:
            self.strategy = SimpleStrategy(self.llm_configs)

    def _setup_api_keys(self) -> None:
        """
        Set up API keys for different providers from config or environment.
        
        The method checks for API keys in the following order:
        1. Config file
        2. Environment variables
        
        """
        api_providers = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "huggingface": "HF_AUTH_TOKEN"
        }
        
        logger.info("=== LLMAdapter Initialization ===")
        
        for provider, env_var in api_providers.items():
            logger.info(f"\nChecking {provider} API key:")
            api_key = config.get_api_key(provider)
            if api_key:
                logger.info(f"- Found in config.yaml, setting to environment")
                os.environ[env_var] = api_key
                if provider == "huggingface":
                    os.environ["HUGGING_FACE_API_KEY"] = api_key
                    logger.info("- Also set HUGGING_FACE_API_KEY")

    def _initialize_llms(self) -> None:
        """Initialize LLM backends based on configurations."""
        for config in self.llm_configs:
            llm_name = config.get("name")
            llm_backend = config.get("backend")
            max_gpu_memory = config.get("max_gpu_memory")
            eval_device = config.get("eval_device")
            hostname = config.get("hostname")

            if not llm_backend:
                continue

            try:
                self._initialize_single_llm(
                    LLMConfig(
                        name=llm_name,
                        backend=llm_backend,
                        max_gpu_memory=max_gpu_memory,
                        eval_device=eval_device,
                        hostname=hostname
                    )
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM {llm_name}: {e}")

        for llm_config in self.llm_configs:
            logger.info(f"Initialized LLM: {llm_config}")

    def _initialize_single_llm(self, config: LLMConfig) -> None:
        """
        Initialize a single LLM based on its configuration.

        Args:
            config: Configuration for the LLM
            
        Example:
            ```python
            config = LLMConfig(
                name="mistral-7b",
                backend="hflocal",
                max_gpu_memory="12GiB"
            )
            adapter._initialize_single_llm(config)
            ```
            
        Raises:
            ValueError: If required API keys are missing
        """
        match config.backend:
            case "hflocal":
                if "HUGGING_FACE_API_KEY" not in os.environ:
                    raise ValueError("HUGGING_FACE_API_KEY not found in config or environment variables")
                self.llms.append(HfLocalBackend(
                    config.name,
                    max_gpu_memory=config.max_gpu_memory,
                    hostname=config.hostname
                ))
                
            case "vllm":
                self.llms.append(VLLMLocalBackend(
                    config.name,
                    max_gpu_memory=config.max_gpu_memory,
                    hostname=config.hostname
                ))
                
            case "ollama":
                self.llms.append(OllamaBackend(
                    config.name,
                    hostname=config.hostname
                ))
                
            case _:
                if config.backend == "google":
                    config.backend = "gemini"
                
                prefix = f"{config.backend}/"
                if not config.name.startswith(prefix):
                    self.llms.append(prefix + config.name)

    def _handle_completion_error(self, error: Exception) -> LLMResponse:
        """
        Handle errors that occur during LLM completion.

        Args:
            error: The exception that occurred

        Returns:
            LLMResponse with appropriate error message
            
        Example:
            ```python
            # Input error
            error = ValueError("Invalid API key provided: sk-...")
            
            # Output LLMResponse
            {
                "response_message": "Error: Invalid or missing API key for the selected model.",
                "error": "Invalid API key provided: sk-****..",
                "finished": True,
                "status_code": 402
            }
            ```
        """
        error_msg = str(error)
        
        # Mask API key in error message
        if "API key provided:" in error_msg:
            key_start = error_msg.find("API key provided:") + len("API key provided: ")
            key_end = error_msg.find(".", key_start)
            if key_end == -1:
                key_end = error_msg.find(" ", key_start)
            if key_end != -1:
                api_key = error_msg[key_start:key_end]
                masked_key = f"{api_key[:2]}****{api_key[-2:]}" if len(api_key) > 4 else "****"
                error_msg = error_msg[:key_start] + masked_key + error_msg[key_end:]

        if "Invalid API key" in error_msg or "API key not found" in error_msg:
            return LLMResponse(
                response_message="Error: Invalid or missing API key for the selected model.",
                error=error_msg,
                finished=True,
                status_code=402
            )
            
        return LLMResponse(
            response_message=f"LLM Error: {error_msg}",
            error=error_msg,
            finished=True,
            status_code=500
        )

    def execute_llm_syscall(
        self,
        llm_syscall,
        temperature: float = 0.0
    ) -> LLMResponse:
        """
        Address request sent from the agent.

        Args:
            llm_syscall: LLMSyscall object containing the request
            temperature: Parameter to control output randomness

        Returns:
            LLMResponse containing the model's response or error information
            
        Example:
            ```python
            # Input
            syscall = LLMSyscall(
                query=LLMQuery(
                    messages=[{"role": "user", "content": "Hello!"}],
                    tools=[{"name": "calculator", "description": "..."}],
                    message_return_type="json"
                )
            )
            
            # Output LLMResponse
            {
                "response_message": "Hello! How can I help you today?",
                "finished": True,
                "tool_calls": None,
                "error": None,
                "status_code": 200
            }
            ```
        """
        try:
            messages = llm_syscall.query.messages
            tools = llm_syscall.query.tools
            ret_type = llm_syscall.query.message_return_type
            selected_llms = llm_syscall.query.llms if llm_syscall.query.llms else self.llm_configs

            llm_syscall.set_status("executing")
            llm_syscall.set_start_time(time.time())
            
            # breakpoint()
            
            model_idxs = self.strategy.get_model_idxs(selected_llms)
            model = self.llms[model_idxs[0]]
            
            if tools:
                tools = pre_process_tools(tools)
            
            messages = self._prepare_messages(
                llm_syscall=llm_syscall,
                model=model,
                messages=messages,
                tools=tools
            )
            
            try:
                completed_response, finished = self._get_model_response(
                    model=model, 
                    messages=messages, 
                    tools=tools,
                    temperature=temperature, 
                    llm_syscall=llm_syscall
                )
            except Exception as e:
                return self._handle_completion_error(e)

            return self._process_response(
                completed_response=completed_response, 
                finished=finished,
                tools=tools, 
                ret_type=ret_type
            )

        except Exception as e:
            return LLMResponse(
                response_message=f"System Error: {str(e)}",
                error=str(e),
                finished=True,
                status_code=500
            )

    def _prepare_messages(self, llm_syscall, model, messages: List[Dict], tools: Optional[List] = None) -> List[Dict]:
        """
        Prepare messages for the LLM, including context restoration and tool formatting.

        Args:
            llm_syscall: The syscall object
            messages: List of message dictionaries
            tools: Optional list of tools

        Returns:
            Prepared list of messages
            
        Example:
            ```python
            # Input
            messages = [
                {"role": "user", "content": "What's 2+2?"}
            ]
            tools = [{
                "name": "calculator",
                "description": "Performs basic math operations"
            }]
            
            # Output
            [
                {"role": "system", "content": "You have access to these tools: calculator..."},
                {"role": "user", "content": "What's 2+2?"}
            ]
            ```
        """
        if self.context_manager:
            pid = llm_syscall.get_pid()
            restored_context = self.context_manager.load_context(
                pid=pid,
                model=model,
                # tokenizer=tokenizer # TODO: Add tokenizer
            )
            messages += [{
                "role": "assistant",
                "content": "" + restored_context,
            }]
            
        # if not isinstance(model, str):
        if tools:
            tools = pre_process_tools(tools)
            messages = tool_calling_input_format(messages, tools)

        return messages

    def _get_model_response(
        self, 
        model: Union[str, HfLocalBackend, VLLMLocalBackend, OllamaBackend],
        messages: List[Dict],
        tools: Optional[List],
        temperature: float,
        llm_syscall
    ) -> Any:
        """
        Get response from the model.

        Args:
            model: The LLM model to use
            messages: Prepared messages
            temperature: Temperature parameter
            llm_syscall: The syscall object

        Returns:
            Model response (string or structured data)
            
        Example:
            ```python
            # Input
            model = "openai/gpt-4"
            messages = [{"role": "user", "content": "Hello!"}]
            temperature = 0.7
            
            # Output (string)
            "Hello! How can I help you today?"
            
            # Or output (with tool calls)
            {
                "tool_calls": [{
                    "id": "call_abc123",
                    "name": "calculator",
                    "arguments": {"operation": "add", "numbers": [2, 2]}
                }]
            }
            ```
        """
        if isinstance(model, str):
            if self.use_context_manager:
                
                pid = llm_syscall.get_pid()
                time_limit = llm_syscall.get_time_limit()
                completed_response, finished = self.context_manager.save_context(
                    model=model, 
                    messages=messages, 
                    tools=tools,
                    temperature=temperature, 
                    pid=pid,
                    time_limit=time_limit
                )
                
                return completed_response, finished
                
            else:
                completed_response = completion(
                    model=model, 
                    messages=messages, 
                    tools=tools, 
                    temperature=temperature
                )
                
                return completed_response.choices[0].message.content, True
        else:
            return (
                self.context_manager.save_context(
                    model=model, 
                    messages=messages, 
                    tools=tools,
                    temperature=temperature, 
                    pid=pid,
                    time_limit=time_limit
                )
                if self.use_context_manager
                else model(
                    messages=messages, 
                    temperature=temperature
                )
            )

    def _process_response(
        self, 
        completed_response: str, 
        finished: bool,
        tools: Optional[List] = None, 
        ret_type: Optional[str] = None
    ) -> LLMResponse:
        """
        Process the model's response into the appropriate format.

        Args:
            response: Raw response from the model
            tools: Optional list of tools
            ret_type: Expected return type ("json" or None)

        Returns:
            Formatted LLMResponse
            
        Example:
            ```python
            # Input
            response = '{"result": "4", "operation": "2 + 2"}'
            tools = None
            ret_type = "json"
            
            # Output LLMResponse
            {
                "response_message": {"result": "4", "operation": "2 + 2"},
                "finished": True,
                "tool_calls": None,
                "error": None,
                "status_code": 200
            }
            
            # Input with tool calls
            response = 'I will use the calculator tool...'
            tools = [{"name": "calculator", ...}]
            
            # Output LLMResponse with tool calls
            {
                "response_message": None,
                "finished": True,
                "tool_calls": [{
                    "id": "call_abc123",
                    "name": "calculator",
                    "arguments": {"operation": "add", "numbers": [2, 2]}
                }],
                "error": None,
                "status_code": 200
            }
            ```
        """
        if tools:
            if tool_calls := parse_tool_calls(completed_response):
                return LLMResponse(
                    response_message=None,
                    tool_calls=tool_calls,
                    finished=finished
                )

        if ret_type == "json":
            completed_response = parse_json_format(completed_response)

        return LLMResponse(response_message=completed_response, finished=finished)
