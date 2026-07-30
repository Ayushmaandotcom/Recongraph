import json
from pathlib import Path
from typing import Any, Mapping
import logging

logger = logging.getLogger(__name__)

class ExplanationTemplateRegistry:
    """
    Loads and applies string interpolation templates for explanation nodes.
    This allows explanation text to evolve over time without modifying deterministic graph logic.
    """
    def __init__(self, templates: dict[str, str] | None = None):
        self._templates: dict[str, str] = templates or {}

    @classmethod
    def from_file(cls, path: Path | str) -> "ExplanationTemplateRegistry":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(data)
        except Exception as e:
            logger.warning(f"Failed to load explanation templates from {path}: {e}")
            return cls({})

    def get_template(self, template_key: str, default: str) -> str:
        return self._templates.get(template_key, default)

    def render(self, template_key: str, variables: Mapping[str, Any], default: str) -> str:
        """
        Renders a template by injecting variables.
        Falls back to a default template if the key is not found.
        """
        template = self.get_template(template_key, default)
        try:
            return template.format_map(_SafeDict(variables))
        except Exception as e:
            logger.error(f"Error rendering template '{template_key}': {e}")
            return default.format_map(_SafeDict(variables))

class _SafeDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"
