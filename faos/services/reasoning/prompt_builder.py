import json
from typing import Dict, Any, List, Optional
from faos.services.security.models import GlobalPolicy

class PromptBuilder:
    """
    Constructs System and User Prompts by merging:
    - Task Intent
    - Execution Context (Evidence)
    - Security Policies (Constraints)
    - Knowledge & Capabilities
    """
    
    def __init__(self, policy: Optional[GlobalPolicy] = None):
        self.policy = policy or GlobalPolicy()
        
    def build_system_prompt(self, base_role: str, capabilities: List[str] = None, knowledge: str = None) -> str:
        """
        Builds the system instruction incorporating roles, capabilities, and constraints.
        """
        prompt = [
            f"# Role",
            base_role,
            ""
        ]
        
        if capabilities:
            prompt.extend([
                "# Capabilities",
                "You have access to the following capabilities/tools indirectly via the FAOS runtime:",
                "\n".join(f"- {cap}" for cap in capabilities),
                ""
            ])
            
        if knowledge:
            prompt.extend([
                "# Domain Knowledge",
                knowledge,
                ""
            ])
            
        prompt.extend([
            "# Constraints",
            f"1. Do not use more than {self.policy.max_tokens_per_task} tokens in your reasoning.",
            "2. Rely ONLY on the provided context evidence. Do not hallucinate data."
        ])
        
        if not self.policy.allow_network_access:
            prompt.append("3. Network access is completely disabled. You cannot fetch live data yourself.")
            
        return "\n".join(prompt)
        
    def build_user_prompt(self, intent: str, context_data: Dict[str, Any]) -> str:
        """
        Builds the user prompt combining the specific intent and the provided context/evidence.
        """
        prompt = [
            "# Task Intent / Role Instruction",
            intent,
            ""
        ]
        
        # Language Requirement directive based on Settings or user preference
        user_params = context_data.get("user_parameters", {})
        lang = (user_params.get("language") or "zh").lower()
        if lang in ("zh", "chinese", "cn", "zh-cn"):
            prompt.extend([
                "# Language Requirement",
                "CRITICAL: Generate all your analysis, reasoning, conclusions, and text in Chinese (中文). Unless the user explicitly asked for English, output entirely in Chinese.",
                ""
            ])
        else:
            prompt.extend([
                "# Language Requirement",
                "CRITICAL: Generate all your analysis, reasoning, conclusions, and text in English. Unless the user explicitly asked for Chinese, output entirely in English.",
                ""
            ])

        # Extract user_parameters to make them explicit directives rather than buried in JSON
        if "user_parameters" in context_data:
            user_params_extracted = context_data.pop("user_parameters")
            if user_params_extracted:
                prompt.extend([
                    "# Global User Directives (Extracted by Planner)",
                    "You MUST strictly follow these global parameters in your response:",
                    json.dumps(user_params_extracted, ensure_ascii=False, indent=2),
                    ""
                ])

        prompt.extend([
            "# Evidence / Context Data",
            "The following structured data was gathered by the runtime providers:"
        ])
        
        # Serialize context data, ignoring huge blobs if we wanted to (but we trust Gemini's 1M window for MVP)
        try:
            context_str = json.dumps(context_data, ensure_ascii=False, indent=2)
            prompt.append("```json\n" + context_str + "\n```")
        except Exception as e:
            prompt.append(f"[Error serializing context: {str(e)}]")
            prompt.append(str(context_data))
            
        return "\n".join(prompt)
