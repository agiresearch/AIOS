from aios.config.config_manager import ConfigManager


def test_config_bootstrap_has_tool_section_or_defaults(tmp_path, monkeypatch):
    """
    Minimal smoke test: ConfigManager should be able to load config via example bootstrap
    and provide tool defaults without crashing.
    """
    # Point config_manager at a temp config directory by monkeypatching __file__-relative resolution.
    # We do this by copying the example config next to a temp config_manager module path simulation
    # is out of scope; instead we validate the default accessors are defensive.
    cfg = ConfigManager()
    tool_cfg = cfg.get_tool_config()
    assert isinstance(tool_cfg, dict)
    assert isinstance(cfg.get_mcp_server_script_path(), str)
    assert isinstance(cfg.get_mcp_clients_config(), list)

