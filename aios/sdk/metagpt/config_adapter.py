# When MetaGPT creates a config, it validates the configuration file.
# However, running on aios does not require MetaGPT's configuration.
# To prevent MetaGPT from throwing errors during execution,
# we will automatically create a fake config to handle MetaGPT's config validation.

try:
    from metagpt.const import CONFIG_ROOT

except ImportError:
    raise ImportError(
        "Could not import metagpt python package. "
        "Please install it with `pip install --upgrade metagpt`."
    )

DEFAULT_CONFIG = """# Full Example: https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml
# Reflected Code: https://github.com/geekan/MetaGPT/blob/main/metagpt/config2.py
llm:
  api_type: "openai"  # or azure / ollama / open_llm etc. Check LLMType for more options
  model: "xxx"  # or gpt-3.5-turbo-1106 / gpt-4-1106-preview
  base_url: "xxx"  # or forward url / other llm url
  api_key: "xxx"
"""

def prepare_metagpt_config():
    """
    Prepare a fake configuration file for MetaGPT if it does not exist.
    This configuration file is used by MetaGPT to validate the configuration.
    """
    target_path = CONFIG_ROOT / "config2.yaml"

    # Create the directory if it does not exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        # If the configuration file already exists, rename it to a backup file
        backup_path = target_path.with_suffix(".bak")
        target_path.rename(backup_path)
        print(f"Existing configuration file backed up at {backup_path}")

    # Write the default configuration to the file
    target_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    print(f"Configuration file initialized at {target_path}")
