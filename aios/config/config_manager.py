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
    
    def save_config(self):
        """Save configuration to yaml file"""
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f)
    
    def update_api_key(self, provider: str, api_key: str):
        """Update API key for specified provider"""
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        self.config["api_keys"][provider] = api_key
        self.save_config()
    
    def update_llm_config(self, model: str, backend: str):
        """Update LLM configuration"""
        if "llm" not in self.config:
            self.config["llm"] = {}
        self.config["llm"]["default_model"] = model
        self.config["llm"]["backend"] = backend
        self.save_config()
    
    def refresh(self):
        """Reload configuration from file"""
        self.load_config()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider, first check config file then environment variables"""
        print(f"\n=== ConfigManager: Getting API key for {provider} ===")
        
        # First try to get from config file
        api_key = None
        if provider == "huggingface":
            api_key = self.config.get("api_keys", {}).get("huggingface", {}).get("auth_token")
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