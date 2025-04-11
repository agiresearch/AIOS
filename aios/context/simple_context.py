# This manages restoring and snapshotting the context.
# The file is used in the BaseLLM class and the RRScheduler class.

from aios.context.base import BaseContextManager

from litellm import completion

from openai import OpenAI

import time
import torch
from typing import Dict, List, Any, Optional, Tuple, Union

from ..llm_core.utils import decode_litellm_tool_calls, merge_messages_with_tools, merge_messages_with_response_format

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

    def get_streaming_completion_response(
            self, 
            model_or_client: Union[str, OpenAI], 
            model_name: str,
            messages: List[Dict[str, str]], 
            tools: Optional[List[Dict[str, Any]]], 
            temperature: float,
            max_tokens: int,
            response_format: Optional[Dict[str, Any]] = None,
            stream: bool = True
        ) -> Any:
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
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "required"
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
                "stream": stream,
                "max_tokens": max_tokens
            }
            
            if tools:
                kwargs["tools"] = tools
                
            if response_format and not stream:
                kwargs["response_format"] = response_format
                
            return model_or_client.chat.completions.create(**kwargs)

    def process_completion_streaming_response(
            self, 
            response: Any, 
            initial_content: str,
            time_limit: float
        ) -> Tuple[str, bool]:
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

    def _is_huggingface_model(self, model) -> bool:
        """
        Check if the model is a HuggingFace model instance.
        
        Args:
            model: The model to check
            
        Returns:
            bool: True if the model is a HuggingFace model, False otherwise
        """
        # Check if model has the HfLocalBackend attributes
        if hasattr(model, 'model') and hasattr(model, 'tokenizer'):
            return True
        return False

    def generate_with_time_limit_hf(
            self, 
            model, 
            messages: List[Dict[str, str]], 
            max_tokens: int,
            temperature: float, 
            pid: int,
            time_limit: float
        ) -> Tuple[str, bool, Dict]:
        """
        Generate text with a HuggingFace model with time limit enforcement.
        
        Args:
            model: The HuggingFace model instance
            messages: List of message dictionaries
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature setting for generation
            time_limit: Maximum time in seconds for generation
            
        Returns:
            Tuple of (result, finished, generation_state)
        """
        
        context_data = self.load_context(pid)
        
        # breakpoint()
        if context_data:
            start_idx = context_data["start_idx"]
            generated_tokens = context_data["generated_tokens"]
            past_key_values = context_data["past_key_values"]
            input_length = context_data["input_length"]
        else:
            start_idx = 0
            
            inputs = model.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )
            
            input_length = inputs["input_ids"].shape[1]
            
            inputs = {k: v.to(model.model.device) for k, v in inputs.items()}
            
            # We'll use a minimum value for sampling, but handle zero separately
            temperature = max(temperature, 1e-7)
            
            # Initialize generation
            generated_tokens = inputs["input_ids"].clone()
            past_key_values = None
        
        # Initialize timing and completion flags
        # breakpoint()
        
        start_time = time.time()
        finished = True
        
        # Generate tokens incrementally with time checking
        for i in range(start_idx, max_tokens):
            # Check time limit
            if time.time() - start_time > time_limit:
                finished = False
                break
            
            # breakpoint()
            
            # Forward pass
            with torch.no_grad():
                outputs = model.model(
                    generated_tokens,
                    return_dict=True,
                    output_attentions=False,
                    output_hidden_states=False
                )
            
            # Get next token logits
            next_token_logits = outputs.logits[:, -1, :]
            
            # Handle token selection based on temperature
            if temperature < 1e-6:  # Effectively zero
                # Greedy decoding - take the token with highest probability
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
            else:
                # Apply temperature for sampling
                next_token_logits = next_token_logits / temperature
                
                # Sample next token
                probs = torch.nn.functional.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            
            # Append to generated tokens
            generated_tokens = torch.cat([generated_tokens, next_token], dim=-1)
            
            # Update past key values
            past_key_values = outputs.past_key_values
            
            # Check if EOS token was generated
            if next_token.item() == model.tokenizer.eos_token_id:
                finished = True
                start_idx = i
                break
            
        # breakpoint()
        
        # Decode the generated tokens
        result = model.tokenizer.decode(generated_tokens[0][input_length:], skip_special_tokens=True)
        
        # breakpoint()
        # Prepare generation state for potential resumption
        # Only store the necessary vectors, not the decoded text
        if not finished:
            self.context_dict[str(pid)] = {
                "generated_tokens": generated_tokens,
                "past_key_values": past_key_values,
                "start_idx": start_idx,
                "input_length": input_length
            }
        else:
            self.clear_context(str(pid))
        
        return result, finished

    
    def generate_response_with_interruption(self, 
            model_name: str, 
            model: Union[str, OpenAI, Any], 
            messages: List[Dict[str, str]], 
            tools: Optional[List[Dict[str, Any]]], 
            message_return_type: str, 
            temperature: float, 
            max_tokens: int,
            pid: Union[int, str], 
            time_limit: float,
            response_format: Optional[Dict[str, Any]] = None
        ) -> Tuple[Any, bool]:
        """
        Save the context of an LLM generation.
        
        This method handles different types of LLM models (string-based, OpenAI client, or HuggingFace)
        and different response types (text, JSON, or tool calls). It manages streaming
        responses and enforces time limits.
        
        Args:
            model_name (str): Name of the model being used
            model (str, OpenAI, or HuggingFace model): The model instance or identifier
            messages (list): List of message dictionaries for the conversation
            tools (list, optional): List of tools available to the model
            message_return_type (str): Expected return type ("text", "json")
            temperature (float): Temperature setting for generation
            max_tokens (int): Maximum number of tokens to generate
            pid (int): Process ID to associate with this context
            time_limit (float): Maximum time in seconds to allow for generation
            response_format (dict, optional): Format specification for the response
            
        Returns:
            tuple: (completed_response, finished)
                - completed_response: The generated text or structured response
                - finished: Boolean indicating if generation completed within time limit
        """
        # Handle HuggingFace models
        if self._is_huggingface_model(model):
            # Use our custom HuggingFace generation with time limit
            if tools:
                messages_with_tools = merge_messages_with_tools(messages, tools)
                completed_response, finished = self.generate_with_time_limit_hf(
                    model=model,
                    messages=messages_with_tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    time_limit=time_limit,
                    pid=pid
                )
            elif message_return_type == "json":
                messages_with_response_format = merge_messages_with_response_format(messages, response_format)
                completed_response, finished = self.generate_with_time_limit_hf(
                    model=model,
                    messages=messages_with_response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    time_limit=time_limit,
                    pid=pid 
                )
            else:
                completed_response, finished = self.generate_with_time_limit_hf(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    time_limit=time_limit,
                    pid=pid
                )
            
            return completed_response, finished
            
        # Handle tool calls (non-streaming)
        if tools:
            response = self._get_completion_response(
                model_or_client=model,
                model_name=model_name,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Process tool calls response
            if isinstance(model, str):
                completed_response = decode_litellm_tool_calls(response)
            else:
                # For OpenAI client, we need to convert the response to the expected format
                completed_response = response
                
            return completed_response, True
        
        # Handle streaming text or JSON responses
        stream_response = self.get_streaming_completion_response(
            model_or_client=model,
            model_name=model_name,
            messages=messages,
            tools=None,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format if message_return_type == "json" else None,
            stream=True
        )
        
        # Get initial content from the last message
        initial_content = messages[-1]["content"] if messages and "content" in messages[-1] else ""
        
        # Process the streaming response
        completed_response, finished = self.process_streaming_completion_response(
            response=stream_response,
            initial_content=initial_content,
            time_limit=time_limit
        )
        
        if not finished:
            # Store the response
            self.context_dict[str(pid)] = completed_response
        else:
            self.clear_context(str(pid))
        return completed_response, finished

    def load_context(self, pid):
        """
        Load a previously saved context for a process.
        
        This method retrieves the saved context for a given process ID and
        handles different model types appropriately, including resuming
        interrupted HuggingFace model generations.
        
        Args:
            pid (int): Process ID to load context for
            model (str, OpenAI, or HuggingFace model): The model instance or identifier
            tokenizer (optional): Tokenizer for decoding context with local models
            
        Returns:
            str or None: The saved context if found, None otherwise
            
        Raises:
            TypeError: If the context and model types are incompatible
        """
        context_data = self.context_dict.get(str(pid), None)
        return context_data

    def clear_context(self, pid):
        """
        Clear the saved context for a process.
        
        Args:
            pid (int): Process ID to clear context for
            
        Returns:
            None
        """
        if str(pid) in self.context_dict:
            self.context_dict.pop(str(pid))
        return
