# This manages restoring and snapshotting the context.
# The file is used in the BaseLLM class and the RRScheduler class.

from aios.context.base import BaseContextManager

from litellm import completion

from openai import OpenAI

import time
from typing import Dict, List, Any, Optional, Tuple, Union

from ..llm_core.utils import decode_litellm_tool_calls

class SimpleContextManager(BaseContextManager):
    """
    A simple context manager for handling LLM context saving and loading.
    
    This class provides functionality to save the current state of an LLM generation,
    load previously saved states, and manage context for different processes.
    
    Example:
        ```python
        context_manager = SimpleContextManager()
        context_manager.start()
        
        # Save context for a process
        response, finished = context_manager.save_context(
            model_name="gpt-4",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            tools=None,
            message_return_type="text",
            temperature=0.7,
            pid=123,
            time_limit=10,
            response_format=None
        )
        
        # Later, load the context
        saved_context = context_manager.load_context(pid=123, model="gpt-4")
        ```
    """
    def __init__(self):
        """
        Initialize the SimpleContextManager with an empty context dictionary.
        """
        BaseContextManager.__init__(self)
        self.context_dict = {}

    def _get_completion_response(self, 
                               model_or_client: Union[str, OpenAI], 
                               model_name: str,
                               messages: List[Dict[str, str]], 
                               tools: Optional[List[Dict[str, Any]]], 
                               temperature: float,
                               response_format: Optional[Dict[str, Any]] = None,
                               stream: bool = True) -> Any:
        """
        Get a completion response from either litellm or OpenAI client.
        
        Args:
            model_or_client: Either a model name string or OpenAI client
            model_name: Name of the model to use
            messages: List of message dictionaries
            tools: Optional list of tools to use
            temperature: Temperature setting for generation
            response_format: Optional format specification for the response
            stream: Whether to stream the response
            
        Returns:
            The completion response object
        """
        if isinstance(model_or_client, str):
            # Use litellm for string-based models
            kwargs = {
                "model": model_or_client,
                "messages": messages,
                "temperature": temperature
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["stream"] = False  # Don't stream tool calls
            else:
                kwargs["stream"] = stream
                
            if response_format and stream:
                kwargs["response_format"] = response_format
                
            return completion(**kwargs)
        else:
            # Use OpenAI client
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            if tools:
                kwargs["tools"] = tools
                
            if response_format and not stream:
                kwargs["response_format"] = response_format
                
            return model_or_client.chat.completions.create(**kwargs)

    def _process_streaming_response(self, 
                                  response: Any, 
                                  initial_content: str,
                                  time_limit: float) -> Tuple[str, bool]:
        """
        Process a streaming response with time limit enforcement.
        
        Args:
            response: The streaming response object
            initial_content: Initial content to start with
            time_limit: Maximum time in seconds to allow for generation
            
        Returns:
            Tuple of (completed_response, finished)
        """
        start_time = time.time()
        completed_response = initial_content
        finished = True
        
        for part in response:
            delta_content = part.choices[0].delta.content or ""
            completed_response += delta_content
            
            if time.time() - start_time > time_limit:
                if part.choices[0].finish_reason is None:
                    finished = False
                break
                
        return completed_response, finished

    def save_context(self, 
                model_name: str, 
                model: Union[str, OpenAI], 
                messages: List[Dict[str, str]], 
                tools: Optional[List[Dict[str, Any]]], 
                message_return_type: str, 
                temperature: float, 
                pid: Union[int, str], 
                time_limit: float,
                response_format: Optional[Dict[str, Any]] = None
            ) -> Tuple[Any, bool]:
        """
        Save the context of an LLM generation.
        
        This method handles different types of LLM models (string-based or OpenAI client)
        and different response types (text, JSON, or tool calls). It manages streaming
        responses and enforces time limits.
        
        Args:
            model_name (str): Name of the model being used
            model (str or OpenAI): The model instance or identifier
            messages (list): List of message dictionaries for the conversation
            tools (list, optional): List of tools available to the model
            message_return_type (str): Expected return type ("text", "json")
            temperature (float): Temperature setting for generation
            pid (int): Process ID to associate with this context
            time_limit (float): Maximum time in seconds to allow for generation
            response_format (dict, optional): Format specification for the response
            
        Returns:
            tuple: (completed_response, finished)
                - completed_response: The generated text or structured response
                - finished: Boolean indicating if generation completed within time limit
                
        Example:
            ```python
            # Using a string-based model
            response, finished = context_manager.save_context(
                model_name="gpt-4",
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                tools=None,
                message_return_type="text",
                temperature=0.7,
                pid=123,
                time_limit=10,
                response_format=None
            )
            
            # Using OpenAI client with tools
            client = OpenAI()
            response, finished = context_manager.save_context(
                model_name="gpt-4",
                model=client,
                messages=[{"role": "user", "content": "What's the weather?"}],
                tools=[{"type": "function", "function": {"name": "get_weather"}}],
                message_return_type="text",
                temperature=0.7,
                pid=456,
                time_limit=30,
                response_format=None
            )
            ```
        """
        # Handle tool calls (non-streaming)
        if tools:
            response = self._get_completion_response(
                model_or_client=model,
                model_name=model_name,
                messages=messages,
                tools=tools,
                temperature=temperature,
                stream=False
            )
            
            # Process tool calls response
            if isinstance(model, str):
                completed_response = decode_litellm_tool_calls(response)
            else:
                # For OpenAI client, we need to convert the response to the expected format
                completed_response = response
                
            # Store the response
            self.context_dict[str(pid)] = completed_response
            return completed_response, True
        
        # Handle streaming text or JSON responses
        stream_response = self._get_completion_response(
            model_or_client=model,
            model_name=model_name,
            messages=messages,
            tools=None,
            temperature=temperature,
            response_format=response_format if message_return_type == "json" else None,
            stream=True
        )
        
        # Get initial content from the last message
        initial_content = messages[-1]["content"] if messages and "content" in messages[-1] else ""
        
        # Process the streaming response
        completed_response, finished = self._process_streaming_response(
            response=stream_response,
            initial_content=initial_content,
            time_limit=time_limit
        )
        
        # Store the response
        self.context_dict[str(pid)] = completed_response
        return completed_response, finished

    def load_context(self, pid, model, tokenizer=None):
        """
        Load a previously saved context for a process.
        
        This method retrieves the saved context for a given process ID and
        handles different model types appropriately.
        
        Args:
            pid (int): Process ID to load context for
            model (str or OpenAI): The model instance or identifier
            tokenizer (optional): Tokenizer for decoding context with local models
            
        Returns:
            str or None: The saved context if found, None otherwise
            
        Raises:
            TypeError: If the context and model types are incompatible
            
        Example:
            ```python
            # Load context for a string-based model
            context = context_manager.load_context(pid=123, model="gpt-4")
            
            # Load context for an OpenAI client
            client = OpenAI()
            context = context_manager.load_context(pid=456, model=client)
            
            # Load context for a local model with tokenizer
            context = context_manager.load_context(
                pid=789, 
                model=local_model,
                tokenizer=local_tokenizer
            )
            ```
        """
        context = self.check_context(pid)
        
        if context is None:
            return None
        
        # Add type checking
        if isinstance(context, str) and not isinstance(model, str):
            raise TypeError("When context is string type, model must also be string type")
        if not isinstance(context, str) and isinstance(model, str):
            raise TypeError("When model is string type, context must also be string type")
        
        if isinstance(model, str):
            return context
        elif isinstance(model, OpenAI):
            return context
        else:
            # For local models that return tensors, decode using tokenizer
            if tokenizer:
                return tokenizer.decode(context)
            return context

    def check_context(self, pid):
        """
        Check if context exists for a given process ID.
        
        Args:
            pid (int): Process ID to check
            
        Returns:
            str or None: The saved context if found, None otherwise
            
        Example:
            ```python
            # Check if context exists
            context = context_manager.check_context(pid=123)
            if context:
                print("Context found:", context)
            else:
                print("No context found for this process")
            ```
        """
        return self.context_dict.get(str(pid), None)

    def clear_context(self, pid):
        """
        Clear the saved context for a process.
        
        Args:
            pid (int): Process ID to clear context for
            
        Returns:
            None
            
        Example:
            ```python
            # Clear context for a process
            context_manager.clear_context(pid=123)
            
            # Verify context was cleared
            assert context_manager.check_context(pid=123) is None
            ```
        """
        if self.check_context(pid):
            self.context_dict.pop(str(pid))
        return
