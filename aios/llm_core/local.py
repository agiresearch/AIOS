from transformers import AutoTokenizer, AutoModelForCausalLM
from litellm import completion

import os

from aios.config.config_manager import config

class HfLocalBackend:
    """
    A backend class for loading and interacting with Hugging Face local models. 
    Supports both local execution and hosted inference if a hostname is provided.
    """

    def __init__(self, model_name, max_gpu_memory=None, eval_device=None, hostname=None):
        """
        Initializes the Hugging Face local backend.

        Args:
            model_name (str): The name of the model to load.
            device (str, optional): The device to load the model on (default is "auto").
            max_gpu_memory (str, optional): Maximum GPU memory allocation.
            hostname (str, optional): The hostname for a hosted HF instance. If provided, 
                                      the model will not be loaded locally.
        """
        print("\n=== HfLocalBackend Initialization ===")
        print(f"Model name: {model_name}")

        self.model_name = model_name
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device if eval_device is not None else "cuda"
        self.hostname = hostname

        # If a hostname is given, then this HF instance is hosted as a web server.
        # Therefore, do not start the AIOS-based HF instance.
        if self.hostname is not None:
            return
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            max_memory=self.max_gpu_memory,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            # use_auth_token=config.get_api_key("huggingface")["auth_token"],
        )
        self.tokenizer.chat_template = "{% for message in messages %}{% if message['role'] == 'user' %}{{ ' ' }}{% endif %}{{ message['content'] }}{% if not loop.last %}{{ ' ' }}{% endif %}{% endfor %}{{ eos_token }}"

    def inference_online(self, messages, temperature, stream=False):
        """
        Sends inference requests to a remote Hugging Face model hosted at the specified hostname.

        Args:
            messages (list): The chat messages for inference.
            temperature (float): Sampling temperature for response generation.
            stream (bool, optional): Whether to stream responses (default is False).
        
        Returns:
            str: The generated response content.
        """
        return completion(
            model="huggingface/" + self.model_name,
            messages=messages,
            temperature=temperature,
            api_base=self.hostname,
        ).choices[0].message.content
    
    def generate(
        self, 
        messages, 
        temperature, 
        max_tokens,
        tools,
        stream=False, 
        time_limit=None
    ):
        
        """
        Generates a response from the locally loaded Hugging Face model or a remote hosted model.

        Args:
            messages (list): The chat messages for inference.
            temperature (float): Sampling temperature for response generation.
            stream (bool, optional): Whether to stream responses (default is False).

        Returns:
            str: The generated response.
        """
        if self.hostname is not None:
            return self.inference_online(messages, temperature, stream=stream)
        
        if stream:
            raise NotImplemented

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )
        
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        temperature = temperature if temperature > 0.5 else 0.5
        response  = self.model.generate(
            **inputs,
            temperature=temperature,
            # max_length=max_tokens,
            max_new_tokens=max_tokens,
            top_k=10,
            num_beams=4,
            early_stopping=True,
            do_sample=True,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id
        )
        
        # breakpoint()
        length = inputs["input_ids"].shape[1]
        result = self.tokenizer.decode(response[0][length:], skip_special_tokens=True)
        return result

class VLLMLocalBackend:
    """
    The VLLMLocalBackend class provides an interface for loading and interacting with vLLM models, 
    supporting both local execution and hosted inference. It allows seamless switching between 
    local model execution and remote API-based inference.

    Attributes:
        model_name (str): The name of the model to be loaded.
        device (str): The device to load the model on (default: "auto").
        max_gpu_memory (Optional[str]): Specifies the maximum GPU memory allocation.
        hostname (Optional[str]): URL for a hosted vLLM instance. If provided, the model 
                                will not be loaded locally.

    Example:
        ```python
        TODO: to be added
        ```
    """

    def __init__(self, model_name, device="auto", max_gpu_memory=None, hostname=None):
        """
        Initializes the vLLM local backend.

        Args:
            model_name (str): The name of the model to load.
            device (str, optional): The device to load the model on (default is "auto").
            max_gpu_memory (str, optional): Maximum GPU memory allocation.
            hostname (str, optional): The hostname for a hosted vLLM instance. If provided, 
                                      the model will not be loaded locally.
        """
        print("\n=== VLLMLocalBackend Initialization ===")
        print(f"Model name: {model_name}")
        
        self.model_name = model_name
        self.device = device
        self.max_gpu_memory = max_gpu_memory
        # self.hostname = hostname
        self.hostname = "http://localhost:8001"

        # If a hostname is given, then this vLLM instance is hosted as a web server.
        # Therefore, do not start the AIOS-based vLLM instance.
        if self.hostname is not None:
            return

        try:
            import vllm

            self.model = vllm.LLM(
                model_name,
                tensor_parallel_size=1 if max_gpu_memory is None else len(max_gpu_memory)
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.sampling_params = vllm.SamplingParams(temperature=temperature)
            
        except ImportError:
            raise ImportError("Could not import vllm Python package"
                              "Please install it with `pip install python`")
        except Exception as err:
            print("Error loading vllm model:", err)

    def inference_online(self, messages, temperature, stream=False):
        breakpoint()
        """
        Sends inference requests to a hosted vLLM instance.

        Args:
            messages (List[Dict[str, str]]): A list of messages in chat format.
            temperature (float): Controls randomness in response generation.
            stream (bool, optional): Whether to use streaming mode (not implemented).

        Returns:
            str: The generated response from the hosted vLLM instance.
        """
        return completion(
            model="hosted_vllm/" + self.model_name,
            messages=messages,
            temperature=temperature,
            api_base=self.hostname,
        ).choices[0].message.content

    def __call__(
        self,
        messages,
        temperature,
        stream=False,
    ):
        """
        Generates a response using the vLLM model.

        Args:
            messages (List[Dict[str, str]]): A list of chat messages.
            temperature (float): Controls randomness in response generation.
            stream (bool, optional): Whether to use streaming mode (not implemented).

        Returns:
            str: The generated response text.
        """
        if self.hostname is not None:
            return self.inference_online(messages, temperature, stream=stream)
        
        assert self.model
        assert self.sampling_params
        # breakpoint()
        if stream:
            raise NotImplemented

        # parameters = vllm.SamplingParams(temperature=temperature)
        prompt     = self.tokenizer.apply_chat_template(messages,
                                                        tokenize=False)
        response   = self.model.generate(prompt, self.sampling_params)
        result     = response[0].outputs[0].text

        return result

class OllamaBackend:
    """
    The OllamaBackend class provides an interface for interacting with Ollama models, 
    supporting both local and remote inference via API requests.

    Attributes:
        model_name (str): The name of the model to be used.
        hostname (str): The API base URL for a hosted Ollama instance. Defaults to "http://localhost:11434".

    Example:
        ```python
        backend = OllamaBackend(model_name="mistral-7b")
        
        messages = [{"role": "user", "content": "Explain quantum entanglement."}]
        response = backend(messages, temperature=0.7)
        print(response)
        ```
    """

    def __init__(self, model_name, device="auto", max_gpu_memory=None, hostname=None):
        """
        Initializes the backend, setting up the model and determining the inference mode.

        Args:
            model_name (str): The name of the model to use.
            device (str, optional): The device for model execution (default is "auto").
            max_gpu_memory (str, optional): Maximum GPU memory allocation (not currently used).
            hostname (str, optional): The hostname for a hosted Ollama instance. If not provided, 
                                      it defaults to "http://localhost:11434".
        """

        print("\n=== OllamaBackend Initialization ===")
        print(f"Model name: {model_name}")
        print(f"Hostname: {hostname or 'http://localhost:11434'}")
        
        self.model_name = model_name
        self.hostname = hostname or "http://localhost:11434"
        
    def __call__(
        self,
        messages,
        temperature,
        # tools=None,
        stream=False,
    ):
        """
        Sends an inference request to the specified Ollama model and returns the generated response.

        Args:
            messages (List[Dict[str, str]]): A list of chat messages in dialogue format.
            temperature (float): Controls randomness in response generation.
            stream (bool, optional): Whether to use streaming mode (not implemented).

        Returns:
            str: The generated response from the Ollama model.
        """
        res = completion(
            model="ollama/" + self.model_name,
            messages=messages,
            temperature=temperature,
            # tools=tools,
            api_base=self.hostname
        ).choices[0].message.content
        # breakpoint()
        return res
