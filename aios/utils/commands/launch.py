from aios.utils import parse_global_args
import os
import sys

def show_available_api_keys():
    print("Available API keys to configure:")
    print("- OPENAI_API_KEY (OpenAI API key)")
    print("- GEMINI_API_KEY (Google Gemini API key)")
    print("- HF_HOME (HuggingFace API token)")

def handle_env_command(args):
    env_file = os.path.expanduser("~/.aios-1/.env")
    
    if args.env_command == "list":
        show_available_api_keys()
            
    elif args.env_command == "set":
        if not args.key or not args.value:
            show_available_api_keys()
            return
            
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

def main():
    parser = parse_global_args()
    args = parser.parse_args()

    if not args.command:
        print("Usage: aios env {list|set}")
        print("Examples:")
        print("  aios env list")
        print("  aios env set OPENAI_API_KEY your_api_key")
        return

    if args.command == "env":
        handle_env_command(args)
    else:
        print("Usage: aios env {list|set}")
        print("Examples:")
        print("  aios env list")
        print("  aios env set OPENAI_API_KEY your_api_key")
