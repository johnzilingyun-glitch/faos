import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PromptRegistry:
    """
    Dynamically loads Markdown/TXT prompt templates from disk.
    Allows easy extension of agent personas without changing code.
    """
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            # Default to the templates directory alongside this file
            current_dir = os.path.dirname(__file__)
            self.templates_dir = os.path.join(current_dir, "templates")
        else:
            self.templates_dir = templates_dir
            
        self._cache: Dict[str, str] = {}
        logger.info(f"PromptRegistry initialized with templates dir: {self.templates_dir}")

    def get_template(self, role: str, language: str = "zh-CN", json_hint: Optional[str] = None) -> str:
        """
        Retrieve a prompt template for a specific role and language.
        If json_hint is provided, appends it to the template to enforce structure.
        """
        lang_suffix = "zh" if language.lower() in ("zh-cn", "zh", "chinese") else "en"
        # Convert role name to filename format (e.g. "Fundamental Analyst" -> "fundamental_analyst")
        role_key = role.strip().replace(" ", "_").replace("-", "_").lower()
        
        # Prefer markdown over txt if both exist
        for ext in ["md", "txt"]:
            filename = f"{role_key}_{lang_suffix}.{ext}"
            path = os.path.join(self.templates_dir, filename)
            
            if path in self._cache:
                return self._append_hint(self._cache[path], json_hint)
                
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    template = f.read()
                    self._cache[path] = template
                    return self._append_hint(template, json_hint)
                    
        # Fallback to English if ZH not found
        if lang_suffix == "zh":
            logger.warning(f"Template for {role} (zh) not found. Falling back to English.")
            return self.get_template(role, language="en", json_hint=json_hint)
            
        raise FileNotFoundError(f"Template not found for role '{role}' in {self.templates_dir}")
        
    def _append_hint(self, template: str, hint: Optional[str]) -> str:
        if hint:
            return template + "\n\nCRITICAL: You MUST output in the following JSON format ONLY:\n```json\n" + hint + "\n```\n"
        return template

# Global registry instance
registry = PromptRegistry()
