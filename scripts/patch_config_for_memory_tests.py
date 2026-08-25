#!/usr/bin/env python3
"""
Patch aios/config/config.yaml for memory integration tests.

Sets:
  - memory.provider = "mem0"
  - memory.auto_extract = true
  - memory.auto_inject = true
  - memory.mem0.embedder uses ollama/nomic-embed-text
  - memory.mem0.vector_store uses chroma with persistence path

Reads from and writes to aios/config/config.yaml by default.
Pass a path argument to override.

Usage:
    python scripts/patch_config_for_memory_tests.py
    python scripts/patch_config_for_memory_tests.py path/to/config.yaml
"""
import sys

import yaml


def patch_config(config_path: str = "aios/config/config.yaml") -> None:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    memory = cfg.setdefault("memory", {})

    # Switch provider to mem0
    memory["provider"] = "mem0"

    # Enable personalization pipeline
    memory["auto_extract"] = True
    memory["auto_inject"] = True

    # Ensure mem0 section is present and correct
    mem0 = memory.setdefault("mem0", {})
    mem0["user_id"] = "default"

    # LLM: ollama (avoids needing an OpenAI API key in CI)
    mem0["llm"] = {
        "provider": "ollama",
        "config": {
            "model": "qwen3:1.7b",
            "ollama_base_url": "http://localhost:11434",
        },
    }

    # Embedder: ollama + nomic-embed-text
    mem0["embedder"] = {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": "http://localhost:11434",
        },
    }

    # Vector store: chroma with persistence
    mem0["vector_store"] = {
        "provider": "chroma",
        "config": {
            "collection_name": "mem0_memories",
            "path": ".mem0/chroma",
        },
    }

    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

    print(f"Patched {config_path}: memory.provider=mem0, "
          f"llm=ollama/qwen3:1.7b, "
          f"embedder=ollama/nomic-embed-text, "
          f"vector_store=chroma (.mem0/chroma)")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "aios/config/config.yaml"
    patch_config(path)
