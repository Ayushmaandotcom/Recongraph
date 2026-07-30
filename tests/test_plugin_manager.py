import pytest
from recongraph.plugins.manager import PluginManager
from recongraph.plugins.sandbox import SandboxedProvider

def test_plugin_manager_discovery():
    manager = PluginManager()
    plugins = manager.discover()
    
    # Core plugins should be discoverable via pyproject.toml
    assert "financial" in plugins
    assert "temporal" in plugins
    assert "tax" in plugins
    assert "vendor" in plugins
    assert "reference" in plugins

def test_plugin_manager_loading():
    manager = PluginManager()
    
    # Load temporal which requires no context
    provider = manager.load_plugin("temporal")
    assert provider is not None
    assert isinstance(provider, SandboxedProvider)
    assert provider.get_name() == "temporal"
    
    # Load with context kwargs
    class MockVendorContext:
        pass
    provider_with_context = manager.load_plugin("vendor", context=MockVendorContext())
    assert provider_with_context is not None
    assert provider_with_context.get_name() == "entity"

def test_plugin_manager_invalid_plugin():
    manager = PluginManager()
    provider = manager.load_plugin("does_not_exist")
    assert provider is None
