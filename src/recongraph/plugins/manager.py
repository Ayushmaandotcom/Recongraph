import sys
import logging
from typing import List

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

from recongraph.plugins.provider import EvidenceProvider
from recongraph.plugins.provider_v2 import EvidenceProviderV2
from recongraph.plugins.sandbox import SandboxedProvider, SandboxedProviderV2

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Discovers and manages dynamic EvidenceProviders via entry points.
    Provides sandboxed wrappers to isolate the engine from plugin crashes.
    """
    
    def __init__(self, group: str = "recongraph.plugins.providers"):
        self.group = group
        self._loaded_plugins: dict[str, EvidenceProvider | EvidenceProviderV2] = {}

    def discover(self) -> List[str]:
        """Returns the names of all discoverable plugins in the entry point group."""
        eps = entry_points(group=self.group)
        return [ep.name for ep in eps]

    def load_plugin(self, name: str, **kwargs) -> EvidenceProvider | EvidenceProviderV2 | None:
        """
        Loads a plugin by its entry point name.
        If successful, returns a Sandboxed version of the provider.
        Any provided kwargs will be passed to the plugin's constructor.
        """
        if name in self._loaded_plugins:
            return self._loaded_plugins[name]

        eps = entry_points(group=self.group)
        matching_eps = [ep for ep in eps if ep.name == name]

        if not matching_eps:
            logger.warning(f"Plugin '{name}' not found in entry point group '{self.group}'.")
            return None
            
        ep = matching_eps[0]
        try:
            plugin_class = ep.load()
            # If it's a class we need to instantiate it
            if isinstance(plugin_class, type):
                provider_instance = plugin_class(**kwargs)
            else:
                provider_instance = plugin_class
                
            # Wrap in sandbox
            if hasattr(provider_instance, 'get_pipeline'):
                sandboxed = SandboxedProviderV2(provider_instance)
            else:
                sandboxed = SandboxedProvider(provider_instance)
                
            self._loaded_plugins[name] = sandboxed
            logger.info(f"Successfully loaded plugin: {name}")
            return sandboxed
            
        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return None

    def load_all(self) -> List[EvidenceProvider | EvidenceProviderV2]:
        """Loads all discoverable plugins."""
        names = self.discover()
        plugins = []
        for name in names:
            p = self.load_plugin(name)
            if p:
                plugins.append(p)
        return plugins
