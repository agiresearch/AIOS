from aios.context.simple_context import SimpleContextManager
from aios.llm_core.routing import RouterStrategy, SequentialRouting, SmartRouting
from aios.llm_core.local import HfLocalBackend
from aios.utils.id_generator import generator_tool_call_id
from cerebrum.llm.apis import LLMQuery, LLMResponse
from litellm import completion
import json
from .utils import merge_messages_with_tools, merge_messages_with_response_format, slash_to_double_underscore, double_underscore_to_slash, decode_litellm_tool_calls, decode_hf_tool_calls
from typing import Dict, Optional, Any, List, Union
import time
import re
import os
from aios.config.config_manager import config
from dataclasses import dataclass
import logging
from typing import Any
import concurrent.futures
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import traceback
import litellm
from .utils import check_availability_for_selected_llm_lists

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from openai import OpenAI, APIError, RateLimitError, AuthenticationError, BadRequestError, APITimeoutError, APIConnectionError

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
        api_key (Optional[str]): API key for the LLM
    
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
    api_key: Optional[str] = None

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
        routing_strategy: Optional[RouterStrategy] = RouterStrategy.Sequential,
    ):
        """
        Initialize the LLMAdapter.

        Args:
            llm_configs: List of LLM configurations
            api_key: API key(s) for the LLM services
            log_mode: Mode of logging the LLM processing status
            use_context_manager: Whether to use context management
            routing_strategy: Strategy for routing requests
        """
        self.log_mode = log_mode
        self.use_context_manager = use_context_manager
        self.context_manager = SimpleContextManager() if use_context_manager else None
        self.llm_configs = llm_configs
        self.llms = []
        
        self._setup_api_keys()
        self._initialize_llms()
        
        routing_strategy = config.get_router_config().get("strategy", RouterStrategy.Sequential)
        
        # breakpoint()
        
        if routing_strategy == RouterStrategy.Sequential:
            self.router = SequentialRouting(
                llm_configs=self.llm_configs
            )
        elif routing_strategy == RouterStrategy.Smart:
            self.router = SmartRouting(
                llm_configs=self.llm_configs,
                bootstrap_url=config.get_router_config().get("bootstrap_url", None)
            )
            
        else:
            raise ValueError(f"Invalid routing strategy: {routing_strategy}")

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
            "huggingface": "HF_AUTH_TOKEN",
            "novita": "NOVITA_API_KEY",
        }
        
        logger.info("=== LLMAdapter Initialization ===")
        
        for provider, env_var in api_providers.items():
            logger.info(f"\nChecking {provider} API key:")
            api_key = config.get_api_key(provider)
            
            if api_key:
                logger.info(f"- Found in config.yaml, setting to environment")
                if provider == "huggingface":
                    os.environ["HF_TOKEN"] = api_key.get("auth_token")
                    os.environ["HF_HOME"] = api_key.get("cache_dir")
                    # os.environ["HUGGING_FACE_API_KEY"] = api_key
                    # logger.info("- Also set HUGGING_FACE_API_KEY")
                else:
                    os.environ[env_var] = api_key
                

    def _initialize_llms(self) -> None:
        """Initialize LLM backends based on configurations."""
        initialized_configs = []
        for config_dict in self.llm_configs:
            try:
                # Validate config dict structure if necessary before creating LLMConfig
                llm_config = LLMConfig(
                    name=config_dict.get("name"),
                    backend=config_dict.get("backend"),
                    max_gpu_memory=config_dict.get("max_gpu_memory"),
                    eval_device=config_dict.get("eval_device"),
                    hostname=config_dict.get("hostname"),
                    api_key=config_dict.get("api_key")
                )
                if not llm_config.name or not llm_config.backend:
                    logger.warning(f"Skipping incomplete LLM config: {config_dict}")
                    continue

                initialized_model = self._initialize_single_llm(llm_config)
                if initialized_model:
                    self.llms.append(initialized_model)
                    initialized_configs.append(llm_config)
                    logger.info(f"Successfully initialized LLM: {llm_config.name} ({llm_config.backend})")
                else:
                    # _initialize_single_llm logs the error, just skip adding
                    pass

            except Exception as e:
                logger.error(f"Failed to process LLM configuration {config_dict.get('name', 'UNKNOWN')}: {e}", exc_info=True)

        # Update self.llm_configs to only contain successfully initialized ones
        self.llm_configs = initialized_configs
        
        self.available_llm_names = [llm_config.name for llm_config in self.llm_configs]
        
        if not self.llms:
            logger.error("No LLMs were successfully initialized. LLMAdapter may not function.")
        else:
            logger.info(f"Total successfully initialized LLMs: {len(self.llms)}")

    def _initialize_single_llm(self, config: LLMConfig) -> Optional[Union[str, HfLocalBackend, OpenAI]]:
        """
        Initialize a single LLM based on its configuration. Logs errors and returns None on failure.

        Args:
            config: Configuration for the LLM
            
        Returns:
            Initialized model instance or identifier, or None if initialization fails.
        """
        try:
            match config.backend:
                case "huggingface" | "hflocal": # Allow alias
                    # HF specific API key check if needed, though HF_TOKEN env var is typical
                    if not os.getenv("HF_TOKEN"):
                        logger.warning(f"HF_TOKEN environment variable not set. May impact private model access for {config.name}")
                    # Add try-except around HfLocalBackend initialization if it can raise specific errors
                    return HfLocalBackend(
                        model_name=config.name,
                        max_gpu_memory=config.max_gpu_memory,
                        eval_device=config.eval_device
                    )
                
                case "vllm" | "sglang":
                    # These use OpenAI compatible endpoints
                    if not config.hostname:
                        logger.error(f"Hostname (base_url) required for {config.backend} backend ({config.name}) but not provided.")
                        return None
                    # OpenAI client init can fail if URL is malformed, though less common.
                    return OpenAI(
                        base_url=config.hostname,
                        api_key=config.api_key or "sk-placeholder" # Use provided key or a placeholder
                    )
                    
                case _:
                    # Handle LiteLLM supported backends
                    backend_name = config.backend
                    # if backend_name == "google":
                    #     backend_name = "gemini" # LiteLLM uses 'gemini'

                    # Check for necessary API keys via environment variables for common LiteLLM backends
                    key_var_map = {
                        "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY",
                        "anthropic": "ANTHROPIC_API_KEY", "groq": "GROQ_API_KEY",
                        # Add others as needed
                    }
                    if backend_name in key_var_map and not os.getenv(key_var_map[backend_name]):
                        # Allow explicit key from config as fallback
                        if config.api_key:
                            os.environ[key_var_map[backend_name]] = config.api_key
                            logger.info(f"Using API key from config for {backend_name}")
                        else:
                            logger.warning(f"Required API key environment variable '{key_var_map[backend_name]}' not set for {config.name} ({backend_name}).")
                            # Depending on strictness, you might return None here or let LiteLLM handle it.
                            # Let LiteLLM handle it for now, it will raise an error later if needed.

                    # Construct the model string for LiteLLM
                    prefix = f"{backend_name}/"
                    if config.name.startswith(prefix):
                        return config.name # Already prefixed
                    else:
                        return prefix + config.name

        except Exception as e:
            logger.error(f"Error initializing LLM {config.name} ({config.backend}): {e}", exc_info=True)
            return None

    def _handle_completion_error(self, error: Exception, model_name: Optional[str] = "Unknown") -> LLMResponse:
        """
        Handle errors that occur during LLM completion, mapping them to LLMResponse.

        Args:
            error: The exception that occurred
            model_name: Name of the model that caused the error

        Returns:
            LLMResponse with appropriate error message and status code
        """
        error_msg = str(error)
        status_code = 500 # Default internal server error
        user_message = f"LLM Error with model '{model_name}': An unexpected error occurred."
        
        # --- Specific OpenAI/LiteLLM Error Handling ---
        # Note: LiteLLM often wraps underlying provider errors.
        if isinstance(error, AuthenticationError) or "invalid api key" in error_msg.lower() or "authentication" in error_msg.lower():
            status_code = 401 # Unauthorized
            user_message = f"Authentication Error with model '{model_name}': Invalid or missing API key."
            # Mask API key if present in the raw error message
            try:
                # Simple regex to find potential keys (sk-..., gsk_..., etc.)
                masked_error_msg = re.sub(r"([a-zA-Z0-9_]{2})[a-zA-Z0-9_.-]+([a-zA-Z0-9_]{4})", r"\1****\2", error_msg)
                error_msg = masked_error_msg
            except Exception:
                pass # Ignore masking errors
        elif isinstance(error, RateLimitError) or "rate limit" in error_msg.lower():
            status_code = 429 # Too Many Requests
            user_message = f"Rate Limit Exceeded for model '{model_name}'. Please try again later."
        elif isinstance(error, BadRequestError) or "bad request" in error_msg.lower() or "invalid parameter" in error_msg.lower() :
            status_code = 400 # Bad Request
            user_message = f"Invalid Request for model '{model_name}'. Check your input parameters (e.g., messages, tools format)."
        elif isinstance(error, APITimeoutError) or "timeout" in error_msg.lower():
            status_code = 408 # Request Timeout
            user_message = f"Request Timed Out for model '{model_name}'. The operation took too long."
        elif isinstance(error, APIConnectionError) or "connection error" in error_msg.lower():
            status_code = 503 # Service Unavailable
            user_message = f"Connection Error with model '{model_name}'. Could not reach the LLM service."
        elif isinstance(error, APIError): # General API error from provider
            status_code = 502 # Bad Gateway (if error seems provider-side)
            user_message = f"API Error from model '{model_name}'. The provider reported an issue."
        elif isinstance(error, litellm.exceptions.NotFound):
            status_code = 404 # Not Found
            user_message = f"Model Not Found: The specified model '{model_name}' could not be found or accessed."
        # --- Add more specific exception checks as needed ---
        logger.error(f"LLM completion error for model '{model_name}': {error_msg}", exc_info=True) # Log full traceback

        return LLMResponse(
            response_message=None,
            error=user_message,
            finished=True,
            status_code=status_code
        )
        
    def execute_llm_syscalls(
        self,
        llm_syscalls: List[LLMQuery],
    ) -> None:
        """
        Execute a batch of LLM syscalls using the configured routing strategy and parallel execution.

        Args:
            llm_syscalls: List of LLMQuery objects

        Returns:
            List of LLMResponse objects corresponding to each input syscall.
            If an error occurs *before* dispatching a syscall, its corresponding response will be an error LLMResponse.
        """
        num_syscalls = len(llm_syscalls)
        if num_syscalls == 0:
            return []

        start_exec_time = time.time()
        logger.info(f"Starting batch execution for {num_syscalls} LLM syscalls...")
        
        if not self.llms:
            logger.error("Cannot execute syscalls: No LLMs were successfully initialized.")
            error_response = LLMResponse(
                response_message=None,
                error="System Error: No LLM backends available.",
                finished=True,
                status_code=503 # Service Unavailable
            )
            for llm_syscall in llm_syscalls:
                llm_syscall.set_status("done")
                llm_syscall.set_response(error_response)
                llm_syscall.set_end_time(time.time())
                llm_syscall.event.set()
            
            return             
        
        
        selected_llm_lists = [syscall.query.llms for syscall in llm_syscalls]
        
        for i, selected_llm_list in enumerate(selected_llm_lists):
            if not selected_llm_list:
                selected_llm_lists[i] = [{"name": llm_config.name, "backend": llm_config.backend} for llm_config in self.llm_configs]
        
        selected_llm_lists_availability = check_availability_for_selected_llm_lists(self.available_llm_names, selected_llm_lists)
        
        executable_llm_syscalls = []
        available_selected_llm_lists = []
        
        # breakpoint()
        
        for i, selected_llm_list_availability in enumerate(selected_llm_lists_availability):
            if not selected_llm_list_availability:
                logger.error(f"Selected LLMs are not available for syscall at index {i}")
                llm_syscall = llm_syscalls[i]
                llm_syscall.set_status("done")
                llm_syscall.set_response(LLMResponse(response_message=None, error="Selected LLMs are not all available. Please check the available LLMs.", finished=True, status_code=500))
                llm_syscall.set_end_time(time.time())
                llm_syscall.event.set()
            else:
                executable_llm_syscalls.append(llm_syscalls[i])
                available_selected_llm_lists.append(selected_llm_lists[i])
        
        queries = [syscall.query.messages for syscall in executable_llm_syscalls]
        
        model_idxs = self.router.get_model_idxs(available_selected_llm_lists, queries)
        
        grouped_tasks = defaultdict(list)

        for i, llm_syscall in enumerate(executable_llm_syscalls):
            model_idx = model_idxs[i]
            
            if model_idx not in grouped_tasks:
                grouped_tasks[model_idx] = []
            grouped_tasks[model_idx].append(llm_syscall)
            
        # --- 3. Parallel Execution using ThreadPoolExecutor ---
        if not grouped_tasks:
            logger.warning("No tasks were grouped for execution.")
            # Fill remaining Nones with a generic routing error if needed
            error_response = LLMResponse(response_message=None, error="System Error: LLM routing failed.", finished=True, status_code=500)
            for llm_syscall in executable_llm_syscalls:
                llm_syscall.set_status("done")
                llm_syscall.set_response(error_response)
                llm_syscall.set_end_time(time.time())
                llm_syscall.event.set()
            return

        # Determine max workers for the outer executor (managing groups)
        max_group_workers = len(grouped_tasks)
        logger.info(f"Processing {len(grouped_tasks)} model groups...")

        # Dictionary to store results keyed by original index
        results_dict = {}

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_group_workers, thread_name_prefix="LLMGroupWorker") as group_executor:
                future_to_group = {
                    group_executor.submit(self._process_batch_for_model, model_idx, tasks): model_idx
                    for model_idx, tasks in grouped_tasks.items()
                }

                for future in concurrent.futures.as_completed(future_to_group):
                    model_idx_completed = future_to_group[future]
                    model_config = self.llm_configs[model_idx_completed] # Get config using index
                    model_name_completed = model_config.name

                    try:
                        # Worker returns a list of (original_index, result_tuple)
                        # where result_tuple is (syscall_object, LLMResponse)
                        group_results = future.result() # Raises exceptions from the worker function
                        
                        for original_idx, (syscall_obj, response) in group_results:
                            results_dict[original_idx] = response # Store the LLMResponse
                            # Update syscall object status based on response
                            if response.finished:
                                syscall_obj.set_status("done")
                            else:
                                # This case implies interruption or streaming, adapt if needed
                                syscall_obj.set_status("suspend") # Or another status?
                            syscall_obj.set_response(response)
                            syscall_obj.set_end_time(time.time())
                            syscall_obj.event.set() # Notify anyone waiting on this specific syscall

                        logger.info(f"Group processing completed for model '{model_name_completed}' (Index {model_idx_completed}). Processed {len(group_results)} tasks.")

                    except Exception as exc:
                        # Handle errors occurring within the _process_batch_for_model worker
                        logger.error(f"Worker thread for model group '{model_name_completed}' (Index {model_idx_completed}) failed: {exc}", exc_info=True)
                        # Assign an error response to all tasks originally assigned to this failed group worker
                        error_response = LLMResponse(
                            response_message=None,
                            error=f"Worker exception: {exc}",
                            finished=True,
                            status_code=500
                        )
                        tasks_in_failed_group = grouped_tasks[model_idx_completed]
                        for failed_original_idx, failed_syscall in tasks_in_failed_group:
                            if failed_original_idx not in results_dict: # Avoid overwriting if processed before crash
                                results_dict[failed_original_idx] = error_response
                                failed_syscall.set_status("error")
                                failed_syscall.set_response(error_response)
                                failed_syscall.set_end_time(time.time())
                                failed_syscall.event.set()


        except Exception as outer_exc:
             # Handle errors during ThreadPoolExecutor setup or management
            logger.error(f"Critical error during batch execution setup: {outer_exc}", exc_info=True)
            error_response = LLMResponse(
                response_message=None,
                error=str(outer_exc),
                finished=True,
                status_code=500
            )
            # Assign error to all tasks that haven't received a result yet
            for llm_syscall in executable_llm_syscalls:
                llm_syscall.set_status("error")
                llm_syscall.set_response(error_response)
                llm_syscall.set_end_time(time.time())
                llm_syscall.event.set()

        end_exec_time = time.time()
        logger.info(f"Batch execution finished for {num_syscalls} syscalls in {end_exec_time - start_exec_time:.2f} seconds.")
        
        return

    
    def _process_batch_for_model(self, model_idx, tasks_with_indices):
        """
        Process a batch of tasks assigned to a specific model index using another ThreadPoolExecutor.

        Args:
            model_idx: Index of the target model configuration.
            tasks_with_indices: List of tuples: [(original_index, llm_syscall), ...]

        Returns:
            List of tuples: [(original_index, (llm_syscall, LLMResponse)), ...]
            Raises exceptions if the inner execution fails critically.
        """
        model_config = self.llm_configs[model_idx]
        logger.info(f"Starting processing for {len(tasks_with_indices)} tasks on model '{model_config.name}' (Index {model_idx}).")
        
        batch_results = []
        max_workers = len(tasks_with_indices)

        try:
            with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"LLMWorker_M{model_idx}") as executor:
                # Map future to original index for result correlation
                future_to_original_index = {
                    executor.submit(self.execute_llm_syscall, model_idx, llm_syscall): original_idx
                    for original_idx, llm_syscall in enumerate(tasks_with_indices)
                }

                for future in concurrent.futures.as_completed(future_to_original_index):
                    original_idx = future_to_original_index[future]
                    syscall_obj = tasks_with_indices[original_idx]

                    try:
                        # execute_llm_syscall now returns (syscall_obj, LLMResponse)
                        result_tuple = future.result()
                        batch_results.append((original_idx, result_tuple))
                    except Exception as exc:
                        # Handle errors from individual execute_llm_syscall calls
                        logger.error(f"Error executing syscall for original index {original_idx} on model '{model_config.name}': {exc}", exc_info=False) # Log less detail maybe
                        # Create an error response for this specific task
                        error_response = self._handle_completion_error(exc, model_config.name)
                        batch_results.append((original_idx, (syscall_obj, error_response))) # Return error response associated with the syscall

        except Exception as batch_exc:
            # Handle errors during the inner ThreadPoolExecutor setup/management
            logger.error(f"Critical error processing batch for model '{model_config.name}': {batch_exc}", exc_info=True)
            # Re-raise the exception to be caught by the outer executor's error handling
            raise batch_exc

        logger.info(f"Finished processing batch for model '{model_config.name}'.")
        return batch_results

    
    def execute_llm_syscall(
        self,
        model_idx,
        llm_syscall,
        temperature: float = 0.0
    ) -> tuple[LLMQuery, LLMResponse]: # Return tuple of (syscall, response)
        """
        Execute a single LLM syscall request. Handles setup, execution, and response processing.

        Args:
            model_idx: Index of the LLM configuration to use.
            llm_syscall: LLMQuery object containing the request.

        Returns:
            A tuple containing the original LLMQuery object and the resulting LLMResponse.
        """
        model_config = self.llm_configs[model_idx]
        model_name = model_config.name
        model_identifier = self.llms[model_idx] # This is the actual model object or string ID
        api_base = model_config.hostname # Use hostname from the validated config

        try:
            # --- Parameter Extraction and Validation ---
            try:
                messages = llm_syscall.query.messages
                tools = llm_syscall.query.tools
                message_return_type = llm_syscall.query.message_return_type
                response_format = llm_syscall.query.response_format
                temperature = llm_syscall.query.temperature if llm_syscall.query.temperature is not None else 1.0 # Default temp if not set
                max_tokens = llm_syscall.query.max_new_tokens if llm_syscall.query.max_new_tokens is not None else 1000 # Default max tokens

                # Basic validation
                if not messages or not isinstance(messages, list):
                    raise ValueError("Syscall query must contain a non-empty list of messages.")
                # Add more validation as needed (e.g., role/content structure)

            except AttributeError as e:
                logger.error(f"Syscall object missing expected attributes: {e}", exc_info=True)
                return (llm_syscall, LLMResponse(
                    response_message=None,
                    error=f"Missing attribute: {e}", finished=True, status_code=400
                ))
            except ValueError as e:
                logger.error(f"Syscall validation failed: {e}", exc_info=True)
                return (llm_syscall, LLMResponse(
                    response_message=None,
                    error=str(e), finished=True, status_code=400
                ))


            llm_syscall.set_status("executing")
            llm_syscall.set_start_time(time.time())

            # --- Tool Preparation ---
            prepared_tools = None
            if tools:
                try:
                    prepared_tools = slash_to_double_underscore(tools)
                except Exception as e:
                    logger.error(f"Error processing tools for syscall: {e}", exc_info=True)
                    return (llm_syscall, LLMResponse(
                        response_message=None,
                        error=f"Tool processing error: {e}", finished=True, status_code=400
                    ))
            
            # --- Model Response Generation ---
            try:
                completed_response, finished = self._get_model_response(
                    model_name=model_name,
                    model=model_identifier,
                    messages=messages,
                    tools=prepared_tools, # Use prepared tools
                    llm_syscall=llm_syscall,
                    api_base=api_base,
                    message_return_type=message_return_type,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                # Handle errors specifically from _get_model_response (API errors, timeouts etc.)
                # The exception 'e' here could be a custom exception raised by _get_model_response
                # or a standard one. _handle_completion_error should classify it.
                logger.warning(f"Model response generation failed for {model_name}: {e}") # Warning level as it's handled
                return (llm_syscall, self._handle_completion_error(e, model_name))

            # --- Response Processing ---
            try:
                processed_response = self._process_response(
                    completed_response=completed_response,
                    finished=finished,
                    tools=tools, # Pass original tools for context if needed by processing logic
                    model=model_identifier, # Pass model identifier if needed
                    message_return_type=message_return_type
                )
                return (llm_syscall, processed_response)

            except Exception as e:
                logger.error(f"Failed to process LLM response for {model_name}: {e}", exc_info=True)
                return (llm_syscall, LLMResponse(
                    response_message=None,
                    error=f"Response processing error: {e}",
                    finished=True, # Mark as finished even if processing failed
                    status_code=500
                ))

        except Exception as e:
            # Catch-all for unexpected errors within the execute_llm_syscall function itself
            logger.error(f"Unexpected critical error during syscall execution for {model_name}: {e}", exc_info=True)
            # Ensure syscall status is updated if possible before returning
            try:
                llm_syscall.set_status("error")
            except Exception:
                pass # Ignore errors during error handling status update

            return (llm_syscall, LLMResponse(
                response_message=None,
                error=f"Unhandled exception: {str(e)}",
                finished=True,
                status_code=500
            ))

    def _get_model_response(
        self, 
        model_name: str,
        model: Union[str, HfLocalBackend, OpenAI],
        messages: List[Dict],
        tools: Optional[List],
        llm_syscall,
        api_base: Optional[str] = None,
        message_return_type: Optional[str] = "text",
        response_format: Optional[Dict[str, Dict]] = None,
        temperature: float = 1.0,
        max_tokens: int = 1000
    ) -> tuple[Union[str, List, Dict], bool]: # Return type depends on success/tool use
        """
        Get response from the specific model backend. Handles API calls and context management.
        Raises exceptions on failure (e.g., API errors, timeouts).

        Args:
            model_name: Name of the model (for logging/errors).
            model: The LLM model instance or LiteLLM identifier string.
            messages: Prepared messages.
            tools: Optional list of tools (with double underscores).
            llm_syscall: The syscall object (for context manager).
            api_base: Optional API base URL.
            message_return_type: Expected return type ("json" or "text").
            response_format: Optional response format specification.
            temperature: Temperature parameter.
            max_tokens: Max tokens parameter.

        Returns:
            Tuple of (model_response, finished_flag). Model response can be str, list (tool calls), or dict (json).
        
        Raises:
            Various exceptions from API calls (APIError, Timeout, etc.) or context manager.
        """
        start_time = time.time()
        logger.debug(f"[{model_name}] Getting model response. Tools: {'Yes' if tools else 'No'}, Type: {message_return_type}, Temp: {temperature}, MaxTokens: {max_tokens}")

        try:
            # --- Context Management Handling ---
            if self.use_context_manager and self.context_manager:
                pid = llm_syscall.get_pid()
                time_limit = llm_syscall.get_time_limit()
                # Assuming generate_response_with_interruption handles its own internal errors
                # or propagates them up. Add try-except here if it can fail before calling the model.
                logger.debug(f"[{model_name}] Using context manager (PID: {pid}, Limit: {time_limit}s)")
                completed_response, finished = self.context_manager.generate_response_with_interruption(
                    model_name=model_name,
                    model=model, # Pass the actual model object/ID
                    messages=messages,
                    tools=tools, # Pass processed tools
                    pid=pid,
                    time_limit=time_limit,
                    message_return_type=message_return_type,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_base=api_base # Pass api_base to context manager if needed
                )
                # The context manager should return the raw response (str, dict, or tool call list)
                # It might raise exceptions if interrupted or if the underlying call fails.
                logger.debug(f"[{model_name}] Context manager returned. Finished: {finished}")
                return completed_response, finished

            # --- Direct Model Call Handling (No Context Manager) ---
            else:
                logger.debug(f"[{model_name}] Calling model directly.")
                completion_kwargs = {
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                # Add tools if provided (use processed tool names)
                if tools:
                    completion_kwargs["tools"] = tools
                    completion_kwargs["tool_choice"] = "auto" # Or "required" if always needed? Let model decide.

                # Add JSON formatting if requested
                # Note: Some models handle "format" kwarg, others "response_format". LiteLLM standardizes.
                if message_return_type == "json":
                    # Standard way via response_format
                    completion_kwargs["response_format"] = {"type": "json_object"}
                    if response_format: # Allow more specific schema if provided
                        # Be careful: merging might be complex depending on provider support
                        logger.warning(f"[{model_name}] Overriding standard JSON format with provided response_format schema. Compatibility depends on model.")
                        completion_kwargs["response_format"] = response_format

                # Add API base if provided (primarily for LiteLLM string models)
                if api_base and isinstance(model, str):
                    completion_kwargs["api_base"] = api_base
                    logger.debug(f"[{model_name}] Using api_base: {api_base}")


                # --- Execute Call Based on Model Type ---
                if isinstance(model, str):
                    # Use LiteLLM completion
                    logger.debug(f"[{model_name}] Calling litellm.completion for model: {model}")
                    # LiteLLM raises specific exceptions on failure
                    response = litellm.completion(model=model, **completion_kwargs)
                    logger.debug(f"[{model_name}] LiteLLM response received.")
                    
                    logger.info(f"Model usage: {response.usage}")
                    # Extract content or tool calls from LiteLLM response
                    message = response.choices[0].message
                    if tools:
                        # if message.tool_calls:
                        # Decode directly here or let _process_response handle?
                        # Let's return the raw tool calls for _process_response
                        # logger.debug(f"[{model_name}] LiteLLM returned tool calls: {message.tool_calls}")
                        # decoded_calls = decode_litellm_tool_calls(response) # Assuming this returns the desired list format
                        return response, True # Return raw tool calls
                    else:
                        # logger.debug(f"[{model_name}] LiteLLM returned content: {message.content[:100]}...")
                        return message.content, True

                elif isinstance(model, OpenAI):
                    # Use OpenAI client (for vLLM, SGLang, or direct OpenAI)
                    logger.debug(f"[{model_name}] Calling OpenAI client for model: {model_name}")
                    # OpenAI client raises specific exceptions
                    response = model.chat.completions.create(
                        model=model_name, # Pass the specific model name if needed by the endpoint
                        **completion_kwargs
                    )
                    logger.debug(f"[{model_name}] OpenAI client response received.")

                    message = response.choices[0].message
                    if message.tool_calls:
                        # logger.debug(f"[{model_name}] OpenAI client returned tool calls: {message.tool_calls}")
                        return message.tool_calls, True # Return raw tool calls
                    else:
                        # logger.debug(f"[{model_name}] OpenAI client returned content: {message.content[:100]}...")
                        return message.content, True

                elif isinstance(model, HfLocalBackend):
                    # Use Hugging Face local backend
                    logger.debug(f"[{model_name}] Calling HfLocalBackend.generate")
                    # Prepare messages specifically for HF backend if needed
                    if tools:
                        # HfLocalBackend expects tools merged into messages
                        final_messages = merge_messages_with_tools(messages, tools)
                        completion_kwargs["messages"] = final_messages
                    elif message_return_type == "json":
                        # HfLocalBackend expects JSON format instruction merged
                        final_messages = merge_messages_with_response_format(messages, response_format or {"type": "json_object"})
                        completion_kwargs["messages"] = final_messages
                    # Remove tool/format kwargs as they are merged into messages for HF
                    completion_kwargs.pop("tools", None)
                    completion_kwargs.pop("tool_choice", None)
                    completion_kwargs.pop("response_format", None)
                    
                    # HfLocalBackend generate might raise its own errors
                    generated_text = model.generate(**completion_kwargs)
                    # logger.debug(f"[{model_name}] HfLocalBackend generated: {generated_text[:100]}...")
                    # HfLocalBackend returns a single string. Tool/JSON decoding happens in _process_response.
                    return generated_text, True


        except (APIError, APITimeoutError, APIConnectionError, RateLimitError, AuthenticationError, BadRequestError) as api_err:
            # Catch specific API/LiteLLM errors and re-raise them for _handle_completion_error
            logger.warning(f"[{model_name}] API call failed: {type(api_err).__name__} - {api_err}")
            raise api_err # Propagate the specific error
        except Exception as e:
            # Catch any other unexpected error during the call
            logger.error(f"[{model_name}] Unexpected error during model response retrieval: {e}", exc_info=True)
            # Wrap in a generic Exception or re-raise? Re-raise for now.
            raise e # Propagate for handling upstream
        finally:
            end_time = time.time()
            logger.debug(f"[{model_name}] _get_model_response took {end_time - start_time:.2f} seconds.")


    def _process_response(
        self,
        completed_response: Union[str, List, Dict], # Raw response: str, list of tool calls (OpenAI/LiteLLM style), or dict (JSON)
        finished: bool,
        tools: Optional[List] = None, # Original tools (with slashes) might be needed for context
        model: Union[str, OpenAI, HfLocalBackend] = None, # Model identifier/object
        message_return_type: Optional[str] = None # "json" or "text"
    ) -> LLMResponse:
        """
        Process the raw model's response into a structured LLMResponse.
        Handles tool call decoding and JSON parsing.

        Args:
            completed_response: Raw response from _get_model_response.
            finished: Flag indicating if the generation finished.
            tools: Original list of tools provided in the request (with slashes).
            model: The model identifier or object used.
            message_return_type: Expected return type ("json" or "text").

        Returns:
            Formatted LLMResponse.
        """
        logger.debug(f"Processing response. Finished: {finished}, Type: {type(completed_response)}, Expected: {message_return_type}")
        
        try:
            # --- Tool Call Handling ---
            # Check if tools were expected *and* if the response looks like tool calls
            if tools:
                # if isinstance(completed_response, list) and all(hasattr(item, 'function') for item in completed_response):
                # Likely OpenAI/LiteLLM style tool calls list
                if isinstance(model, str) or isinstance(model, OpenAI):
                    logger.debug("Processing list of tool calls (OpenAI/LiteLLM style).")
                    try:
                        # Need to convert OpenAI/LiteLLM ToolCall objects to our dict format
                        decoded_calls = decode_litellm_tool_calls(completed_response) # Wrap for decoder
                        final_tool_calls = double_underscore_to_slash(decoded_calls)
                        logger.debug(f"Decoded tool calls: {final_tool_calls}")
                        return LLMResponse(
                            response_message=None,
                            tool_calls=final_tool_calls,
                            finished=finished,
                            status_code=200
                        )
                    except Exception as e:
                        logger.error(f"Error decoding LiteLLM/OpenAI tool calls: {e}", exc_info=True)
                        return LLMResponse(
                            response_message=None,
                            error=f"Tool call decoding error: {e}",
                            finished=True, # Treat as finished with error
                            status_code=500
                        )
                elif isinstance(model, HfLocalBackend) and isinstance(completed_response, str):
                    # HF models return text that needs parsing for tool calls
                    logger.debug("Attempting to decode tool calls from HfLocalBackend string response.")
                    try:
                        # decode_hf_tool_calls expects the raw string
                        tool_calls = decode_hf_tool_calls(completed_response)
                        if tool_calls: # Check if decoding was successful
                            tool_calls = double_underscore_to_slash(tool_calls)
                            logger.debug(f"Decoded HF tool calls: {tool_calls}")
                            return LLMResponse(
                                response_message=None, # No text message if tools were called
                                tool_calls=tool_calls,
                                finished=finished, # Usually True for HF unless streaming implemented differently
                                status_code=200
                            )
                        else:
                            # Model tried to call tools but failed, or just generated text?
                            logger.warning("HfLocalBackend response received when tools expected, but decode_hf_tool_calls returned empty. Treating as text.")
                            # Fall through to text/JSON processing
                            pass
                    except Exception as e:
                        logger.error(f"Error decoding tool calls from HfLocalBackend response: {e}", exc_info=True)
                        return LLMResponse(
                            response_message=None,
                            error=f"Tool call decoding error: {e}",
                            finished=True,
                            status_code=500
                        )
                # else: Handle cases where tools were expected but response isn't recognized tool format?
                #      For now, fall through to text/JSON processing.

            # --- Plain Text Response Handling ---
            if isinstance(completed_response, str):
                logger.debug("Processing as plain text response.")
                return LLMResponse(
                    response_message=completed_response,
                    finished=finished,
                    status_code=200
                )

            # --- Fallback for Unexpected Types ---
            logger.warning(f"Unexpected response type received in _process_response: {type(completed_response)}. Content: {str(completed_response)[:200]}...")
            # Attempt to convert to string as a last resort
            try:
                fallback_message = str(completed_response)
                return LLMResponse(
                    response_message=fallback_message,
                    finished=finished, # Assume finished?
                    status_code=200, # Or maybe an error code? Let's assume success but log warning.
                    error="Warning: Unexpected response type processed."
                )
            except Exception as str_e:
                logger.error(f"Could not convert unexpected response type {type(completed_response)} to string: {str_e}")
                return LLMResponse(
                    response_message=None,
                    error=f"Cannot handle type {type(completed_response)}",
                    finished=True,
                    status_code=500
                )

        except Exception as e:
            # Catch-all for errors during the processing itself
            logger.error(f"Critical error during response processing: {e}", exc_info=True)
            return LLMResponse(
                response_message=None,
                error=f"Unhandled processing exception: {e}",
                finished=True, # Mark as finished even if processing failed
                status_code=500
            )
