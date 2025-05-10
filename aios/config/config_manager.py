import os
import yaml
from typing import Any, Optional

class ConfigManager:
    """
    A singleton class that manages configuration settings for the AIOS system.
    
    Class Variables:
        _instance (ConfigManager): Singleton instance of the class
        config_path (str): Path to the configuration file
        config (dict): Dictionary containing all configuration settings
    
    Example:
        # Get the global config instance
        config_manager = ConfigManager()
        
        # Update API key
        config_manager.update_api_key("openai", "sk-...")
        
        # Get LLM configuration
        llm_config = config_manager.get_llms_config()
    """
    _instance = None
    
    def __new__(cls):
        """
        Ensures only one instance of ConfigManager is created (Singleton pattern).
        
        Returns:
            ConfigManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initializes the ConfigManager if not already initialized.
        Loads configuration from the default config.yaml file.
        """
        if not hasattr(self, 'config'):
            # Configuration file should be at aios/config/config.yaml
            self.config_path = os.path.join(
                os.path.dirname(__file__),  # aios/config directory
                'config.yaml'
            )
            self.load_config()
    
    def load_config(self):
        """
        Loads configuration from the YAML file.
        
        Raises:
            FileNotFoundError: If the config file doesn't exist
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def save_config(self):
        """
        Saves the current configuration to the YAML file.
        """
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f)
    
    def update_api_key(self, provider: str, api_key: str):
        """
        Updates the API key for a specified provider in the configuration.
        
        Args:
            provider (str): The name of the API provider (e.g., "openai", "anthropic")
            api_key (str): The API key to be stored
            
        Example:
            config_manager.update_api_key("openai", "sk-...")
        """
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        self.config["api_keys"][provider] = api_key
        self.save_config()
    
    def update_llm_config(self, model: str, backend: str):
        """
        Updates the default LLM configuration.
        
        Args:
            model (str): The model identifier
            backend (str): The backend service to use
            
        Example:
            config_manager.update_llm_config("gpt-4", "openai")
        """
        if "llm" not in self.config:
            self.config["llm"] = {}
        self.config["llm"]["default_model"] = model
        self.config["llm"]["backend"] = backend
        self.save_config()
    
    def refresh(self):
        """
        Reloads the configuration from the file to get the latest changes.
        """
        self.load_config()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieves the API key for a specified provider, checking both config file and environment variables.
        
        Args:
            provider (str): The name of the API provider (e.g., "openai", "anthropic")
            
        Returns:
            Optional[str]: The API key if found, None otherwise
            
        Example:
            api_key = config_manager.get_api_key("openai")
            if api_key:
                # Use the API key
                pass
        """
        print(f"\n=== ConfigManager: Getting API key for {provider} ===")
        
        # First try to get from config file
        api_key = None
        if provider == "huggingface":
            api_key = self.config.get("api_keys", {}).get("huggingface", {})
        else:
            api_key = self.config.get("api_keys", {}).get(provider)
        
        print(f"- Checking config.yaml: {'Found' if api_key else 'Not found'}")
        
        # If not found in config, try environment variables
        if not api_key:
            env_var_map = {
                "openai": "OPENAI_API_KEY",
                "gemini": "GEMINI_API_KEY", 
                "groq": "GROQ_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "huggingface": "HF_AUTH_TOKEN"
            }
            if provider in env_var_map:
                env_var = env_var_map[provider]
                api_key = os.environ.get(env_var)
                print(f"- Checking environment variable {env_var}: {'Found' if api_key else 'Not found'}")
            
        return api_key
    
    def get_llms_config(self) -> dict:
        """
        Retrieves the LLM configuration settings.
        
        Returns:
            dict: Dictionary containing LLM configurations
            
        Example:
            llm_config = config_manager.get_llms_config()
            default_model = llm_config.get("default_model")
        """
        return self.config.get('llms', {})
    
    def get_router_config(self) -> dict:
        """
        Retrieves the router configuration settings.
        
        Returns:
            dict: Dictionary containing router configurations
        """
        return self.config.get("llms", {}).get("router", {})
    
    def get_storage_config(self) -> dict:
        """
        Retrieves the storage configuration settings.
        
        Returns:
            dict: Dictionary containing storage configurations
            
        Example:
            storage_config = config_manager.get_storage_config()
            storage_path = storage_config.get("path")
        """
        return self.config.get("storage", {})
    
    def get_memory_config(self) -> dict:
        """
        Retrieves the memory configuration settings.
        
        Returns:
            dict: Dictionary containing memory configurations
            
        Example:
            memory_config = config_manager.get_memory_config()
            memory_type = memory_config.get("type")
        """
        return self.config.get("memory", {})

    def get_tool_config(self) -> dict:
        """
        Retrieves the tool configuration settings.
        
        Returns:
            dict: Dictionary containing tool configurations
            
        Example:
            tool_config = config_manager.get_tool_config()
            enabled_tools = tool_config.get("enabled")
        """
        return self.config.get("tool", {})
    
    def get_mcp_server_script_path(self) -> str:
        """
        Retrieves the path to the MCP server script.
        """
        return os.path.join(os.getcwd(), self.config.get("tool", {}).get("mcp_server_script_path"))
    
    def get_scheduler_config(self) -> dict:
        """
        Retrieves the scheduler configuration settings.
        
        Returns:
            dict: Dictionary containing scheduler configurations
            
        Example:
            scheduler_config = config_manager.get_scheduler_config()
            max_tasks = scheduler_config.get("max_concurrent_tasks")
        """
        return self.config.get("scheduler", {})
    
    def get_agent_factory_config(self) -> dict:
        """
        Retrieves the agent factory configuration settings.
        
        Returns:
            dict: Dictionary containing agent factory configurations
            
        Example:
            factory_config = config_manager.get_agent_factory_config()
            agent_types = factory_config.get("available_agents")
        """
        return self.config.get("agent_factory", {})
    
    def get_server_config(self) -> dict:
        """
        Retrieves the server configuration settings.
        
        Returns:
            dict: Dictionary containing server configurations
            
        Example:
            server_config = config_manager.get_server_config()
            host = server_config.get("host")
            port = server_config.get("port")
        """
        return self.config.get("server", {})
    
    # def get_kernel_config(self) -> dict:
    #     """Get kernel configuration"""
    #     return self.config.get("kernel", {})

# Global config instance
config = ConfigManager() 