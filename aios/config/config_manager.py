import os
import yaml
from typing import Any, Optional

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'config'):
            # Configuration file should be at aios/config/config.yaml
            self.config_path = os.path.join(
                os.path.dirname(__file__),  # aios/config directory
                'config.yaml'
            )
            self.load_config()
    
    def load_config(self):
        """Load configuration from yaml file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def refresh(self):
        """Reload configuration from file"""
        self.load_config()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        print(f"Trying to get API key for provider: {provider}")
        print(f"Current config: {self.config}")
        
        api_key = None
        if provider == "huggingface":
            api_key = self.config.get("api_keys", {}).get("huggingface", {}).get("auth_token")
        else:
            api_key = self.config.get("api_keys", {}).get(provider)
        
        print(f"Found API key: {'[SET]' if api_key else '[NOT SET]'}")
        return api_key
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration"""
        llm_config = self.config.get('llm', {})
        if not llm_config:
            # Provide default configuration
            llm_config = {
                "default_model": "gpt-4",
                "max_new_tokens": 256,
                "backend": "openai",
                "max_gpu_memory": None,
                "eval_device": "cuda:0",
                "log_mode": "console"
            }
        return llm_config
    
    def get_kernel_config(self) -> dict:
        """Get kernel configuration"""
        return self.config.get("kernel", {})

# Global config instance
config = ConfigManager() 