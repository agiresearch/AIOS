from aios.utils import parse_global_args
from aios.config.config_manager import config
import os
import sys
import requests

def show_available_api_keys():
    print("Available API keys to configure:")
    print("- OPENAI_API_KEY (OpenAI API key)")
    print("- GEMINI_API_KEY (Google Gemini API key)")
    print("- GROQ_API_KEY (Groq API key)")
    print("- HF_AUTH_TOKEN (HuggingFace authentication token)")
    print("- HF_HOME (Optional: Path to store HuggingFace models)")

def handle_env_command(args):
    env_file = os.path.expanduser("~/.aios-1/.env")
    
    if args.env_command in ["list", "set"]:
        if os.path.exists(env_file) and os.path.getsize(env_file) > 0:
            print("Current environment variables:")
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        name = line.split('=')[0]
                        print(f"{name}=****")
        else:
            show_available_api_keys()
            
        if args.env_command == "set" and args.key and args.value:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(env_file), exist_ok=True)
            
            # Read existing variables
            env_vars = {}
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            env_vars[k] = v
            
            # Update or add new variable
            env_vars[args.key] = args.value
            
            # Write back to file
            with open(env_file, 'w') as f:
                for k, v in env_vars.items():
                    f.write(f"{k}={v}\n")
            print(f"Environment variable {args.key} has been set")
    else:
        print("Usage: aios env {list|set}")
        print("Examples:")
        print("  aios env list")
        print("  aios env set OPENAI_API_KEY your_api_key")

def handle_refresh_command():
    """Handle configuration refresh command"""
    try:
        print("\n=== AIOS Configuration ===")
        
        # Refresh configuration
        config.refresh()
        
        # Get server URL from config
        host = config.config.get('server', {}).get('host', 'localhost')
        port = config.config.get('server', {}).get('port', 8000)
        server_url = f"http://{host}:{port}"
        
        # Display current API key status (masked)
        print("\nAPI Keys Status:")
        for provider, key in config.config.get('api_keys', {}).items():
            if isinstance(key, dict):
                print(f"- {provider}:")
                for k, v in key.items():
                    if v:
                        masked_value = "****" + v[-4:] if len(v) > 4 else "****"
                        print(f"  {k}: {masked_value}")
                    else:
                        print(f"  {k}: [NOT SET]")
            else:
                if key:
                    masked_key = "****" + key[-4:] if len(key) > 4 else "****"
                    print(f"- {provider}: {masked_key}")
                else:
                    print(f"- {provider}: [NOT SET]")
        
        # Notify kernel to refresh configuration
        try:
            response = requests.post(
                f"{server_url}/core/refresh",
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Kernel configuration refreshed: {result['message']}")
            else:
                print(f"\n❌ Failed to refresh kernel configuration: {response.text}")
        except requests.exceptions.ConnectionError:
            print("\n⚠️ Warning: Could not connect to kernel. Is the kernel running?")
            print("To start the kernel, run: python runtime/launch_kernel.py start")
        except Exception as e:
            print(f"\n❌ Error communicating with kernel: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error refreshing configuration: {e}")

def main():
    parser = parse_global_args()
    args = parser.parse_args()

    if not args.command:
        print("Usage: aios {env|refresh}")
        print("Examples:")
        print("  aios env list")
        print("  aios env set OPENAI_API_KEY your_api_key")
        print("  aios refresh")
        return

    if args.command == "env":
        handle_env_command(args)
    elif args.command == "refresh":
        handle_refresh_command()
    else:
        print("Usage: aios {env|refresh}")
        print("Examples:")
        print("  aios env list")
        print("  aios env set OPENAI_API_KEY your_api_key")
        print("  aios refresh")
